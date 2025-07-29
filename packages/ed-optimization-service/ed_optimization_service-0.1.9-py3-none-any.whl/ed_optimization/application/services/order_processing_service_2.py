from datetime import UTC, datetime, timedelta
from uuid import UUID

from ed_domain.core.aggregate_roots.order import Order
from ed_domain.core.entities.waypoint import Waypoint, WaypointStatus
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_optimization.application.contracts.infrastructure.api.abc_api import \
    ABCApi
from ed_optimization.application.contracts.infrastructure.cache.abc_cache import \
    ABCCache
from ed_optimization.application.contracts.infrastructure.google.abc_google_maps_route_api import \
    ABCGoogleMapsRoutesAPI
from ed_optimization.application.contracts.infrastructure.google.types import \
    RawWaypoint
from ed_optimization.application.services.business_service import \
    BusinessService
from ed_optimization.application.services.consumer_service import \
    ConsumerService
from ed_optimization.application.services.delivery_job_service import \
    DeliveryJobService
from ed_optimization.application.services.location_service import \
    LocationService
from ed_optimization.application.services.waypoint_service import (
    CreateWaypointModel, WaypointService)
from ed_optimization.common.logging_helpers import get_logger

LOG = get_logger()
RADIUS_OF_EARTH_KM = 6371
MAX_BATCH_SIZE = 2
MAX_WAIT_TIME = timedelta(minutes=5)
MAX_MATCH_TIME_DELTA_SECONDS = 1800
MAX_MATCH_DISTANCE_KM = 5


class OrderProcessingService:
    def __init__(
        self,
        uow: ABCAsyncUnitOfWork,
        cache: ABCCache[list[Order]],
        api: ABCApi,
        google_maps_api: ABCGoogleMapsRoutesAPI,
    ):
        self._cache_key = "pending_delivery_job"
        self._uow = uow
        self._cache = cache
        self._api = api
        self._google_maps_api = google_maps_api

        self._business_service = BusinessService(uow)
        self._consumer_service = ConsumerService(uow)
        self._location_service = LocationService(uow)
        self._delivery_job_service = DeliveryJobService(uow)
        self._waypoint_service = WaypointService(uow)

    async def process_incoming_order(self, order: Order) -> None:
        LOG.info(f"Service received order ID: {order.id}")
        pending_orders = await self._get_pending_orders()

        if not pending_orders:
            LOG.info("No pending orders, initializing queue with current order.")
            await self._save_pending_orders([order])
            return

        oldest_order = pending_orders[0]
        # Ensure 'create_datetime' exists in Order for this check
        if datetime.now(UTC) - oldest_order.create_datetime > MAX_WAIT_TIME:
            LOG.info(
                f"Oldest order (ID: {oldest_order.id}) too old. Forcing batch flush."
            )
            await self._flush_pending_orders(pending_orders + [order])
            return

        if await self._is_match(order, pending_orders):
            LOG.info(
                f"Order (ID: {order.id}) matches current batch. Appending.")
            pending_orders.append(order)
        else:
            LOG.info(
                f"Order (ID: {order.id}) does not match current batch. Flushing {len(pending_orders)} orders and starting new batch."
            )
            await self._flush_pending_orders(pending_orders)
            pending_orders = [order]

        if len(pending_orders) >= MAX_BATCH_SIZE:
            LOG.info(
                f"Batch size threshold ({MAX_BATCH_SIZE}) reached. Flushing {len(pending_orders)} orders."
            )
            await self._flush_pending_orders(pending_orders)
        else:
            await self._save_pending_orders(pending_orders)

    async def _is_match(self, order: Order, pending_orders: list[Order]) -> bool:
        if not pending_orders:
            return True

        existing_order = pending_orders[0]

        time_delta_seconds = abs(
            (
                order.latest_time_of_delivery - existing_order.latest_time_of_delivery
            ).total_seconds()
        )

        if time_delta_seconds > MAX_MATCH_TIME_DELTA_SECONDS:
            LOG.debug(
                f"Time delta {time_delta_seconds}s exceeds {MAX_MATCH_TIME_DELTA_SECONDS}s. No match."
            )
            return False

        business1 = await self._business_service.get(existing_order.business_id)
        business2 = await self._business_service.get(order.business_id)
        assert business1 is not None and business2 is not None

        loc1 = await self._location_service.get(business1.location_id)
        loc2 = await self._location_service.get(business2.location_id)
        assert loc1 is not None and loc2 is not None

        route_information = await self._google_maps_api.get_route(loc1, loc2)

        distance_km = round(route_information["distance_meters"] / 1000, 2)

        if distance_km > MAX_MATCH_DISTANCE_KM:
            LOG.debug(
                f"Distance {distance_km:.2f} km exceeds {MAX_MATCH_DISTANCE_KM} km. No match."
            )
            return False

        LOG.info(
            f"Order {order.id} matches batch with order {existing_order.id}: time_delta={time_delta_seconds}s, distance={distance_km:.2f}km."
        )
        return True

    async def _flush_pending_orders(self, orders: list[Order]) -> None:
        LOG.info(f"Flushing {len(orders)} orders into a DeliveryJob.")

        raw_pick_up_waypoints_data = []
        raw_drop_off_waypoints_data = []

        for order in orders:
            business = await self._business_service.get(order.business_id)
            assert business is not None

            consumer = await self._consumer_service.get(order.consumer_id)
            assert consumer is not None

            business_loc = await self._location_service.get(business.location_id)
            consumer_loc = await self._location_service.get(consumer.location_id)

            raw_pick_up_waypoints_data.append(
                {
                    "order_id": order.id,
                    "eta": order.latest_time_of_delivery,
                    "location": business_loc,
                }
            )
            raw_drop_off_waypoints_data.append(
                {
                    "order_id": order.id,
                    "eta": order.latest_time_of_delivery,
                    "location": consumer_loc,
                }
            )

        delivery_job = await self._delivery_job_service.create_default()
        optimized_waypoints, estimated_distance_km, estimated_time_minutes = (
            await self._optimize_waypoints_with_Maps(
                raw_pick_up_waypoints_data, delivery_job.id
            )
        )

        delivery_job.waypoints = optimized_waypoints
        delivery_job.estimated_time_in_minutes = estimated_time_minutes
        delivery_job.estimated_distance_in_kms = estimated_distance_km

        await self._delivery_job_service.save(delivery_job)

    async def _optimize_waypoints_with_Maps(
        self,
        raw_waypoints: list[RawWaypoint],
        delivery_job_id: UUID,
    ) -> tuple[list[Waypoint], float, int]:
        route_information = await self._google_maps_api.optimize_routes(raw_waypoints)
        assert route_information is not None

        total_distance_km = round(
            route_information["distance_meters"] / 1000, 2)
        total_time_minutes = round(route_information["duration_seconds"] / 60)
        reordered_waypoints = route_information["waypoints"]

        final_waypoints: list[Waypoint] = []
        for i, wp_data in enumerate(reordered_waypoints):
            final_waypoints.append(
                await self._waypoint_service.create_waypoint(
                    CreateWaypointModel(
                        delivery_job_id=delivery_job_id,
                        order_id=wp_data["order_id"],
                        sequence=i,
                        expected_arrival_time=wp_data["expected_arrival_time"],
                        waypoint_type=wp_data["waypoint_type"],
                        waypoint_status=WaypointStatus.PENDING,
                    )
                )
            )

        LOG.info(
            f"Waypoint optimization completed. Est. Distance: {total_distance_km:.2f} km, Est. Time: {total_time_minutes:.0f} min."
        )
        return final_waypoints, total_distance_km, int(total_time_minutes)

    async def _get_pending_orders(self) -> list[Order]:
        if pending := await self._cache.get(self._cache_key):
            return pending
        return []

    async def _save_pending_orders(self, orders: list[Order]) -> None:
        await self._cache.set(self._cache_key, orders)
        LOG.info(f"Saved {len(orders)} orders to pending cache.")
