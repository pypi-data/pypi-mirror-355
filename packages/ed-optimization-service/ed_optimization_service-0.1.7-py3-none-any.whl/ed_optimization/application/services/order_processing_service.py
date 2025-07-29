import asyncio
from datetime import UTC, datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from uuid import UUID

from ed_domain.core.aggregate_roots import Location
from ed_domain.core.aggregate_roots.order import Order
from ed_domain.core.entities.waypoint import (Waypoint, WaypointStatus,
                                              WaypointType)
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork

from ed_optimization.application.contracts.infrastructure.cache.abc_cache import \
    ABCCache
from ed_optimization.application.contracts.infrastructure.google.abc_google_maps_route_api import \
    ABCGoogleMapsRoutesAPI
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
        google_maps_api: ABCGoogleMapsRoutesAPI,
    ):
        self._cache_key = "pending_delivery_job"
        self._uow = uow
        self._cache = cache
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
        """
        Determines if a new order matches the criteria for the current batch of pending orders.
        Uses Google Maps Distance Matrix API for accurate distance/duration, with Haversine as fallback.
        """
        if not pending_orders:
            return True

        # Compare with the first order in the batch
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

        distance_km = float("inf")
        duration_seconds = float("inf")

        # --- Conceptual Google Maps API call (uncomment and implement with real client) ---
        if self._google_maps_api:
            try:
                travel_info = await self._get_Maps_travel_info(loc1, loc2)
                if travel_info:
                    distance_km = travel_info["distance_km"]
                    duration_seconds = travel_info["duration_seconds"]
                    LOG.debug(
                        f"Google Maps: Distance {distance_km:.2f} km, Duration {duration_seconds:.0f} s."
                    )
            except Exception as e:
                LOG.error(
                    f"Error fetching Google Maps travel info: {e}. Falling back to Haversine."
                )
        else:
            LOG.debug(
                "Google Maps client not available. Using Haversine distance.")

        if distance_km == float("inf"):
            distance_km = self._haversine_distance_km(loc1, loc2)
            LOG.debug(f"Haversine: Distance {distance_km:.2f} km.")

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
        """
        Flushes a batch of orders, creating a DeliveryJob via the core API.
        Optimizes waypoints using Google Maps Routes API (conceptual).
        """
        LOG.info(f"Flushing {len(orders)} orders into a DeliveryJob.")

        raw_waypoints_data = []
        for order in orders:
            business = await self._business_service.get(order.business_id)
            assert business is not None

            consumer = await self._consumer_service.get(order.consumer_id)
            assert consumer is not None

            business_loc = await self._location_service.get(business.location_id)
            customer_loc = await self._location_service.get(consumer.location_id)

            raw_waypoints_data.append(
                {
                    "order_id": order.id,
                    "type": WaypointType.PICK_UP,
                    "eta": order.latest_time_of_delivery,
                    "location": business_loc,
                }
            )
            raw_waypoints_data.append(
                {
                    "order_id": order.id,
                    "type": WaypointType.DROP_OFF,
                    "eta": order.latest_time_of_delivery,
                    "location": customer_loc,
                }
            )

        delivery_job = await self._delivery_job_service.create_default()
        optimized_waypoints, estimated_distance_km, estimated_time_minutes = (
            await self._optimize_waypoints_with_Maps(
                raw_waypoints_data, delivery_job.id
            )
        )

        delivery_job.waypoints = optimized_waypoints
        delivery_job.estimated_time_in_minutes = estimated_time_minutes
        delivery_job.estimated_distance_in_kms = estimated_distance_km

        await self._delivery_job_service.save(delivery_job)

    async def _get_pending_orders(self) -> list[Order]:
        if pending := await self._cache.get(self._cache_key):
            return pending
        return []

    async def _save_pending_orders(self, orders: list[Order]) -> None:
        await self._cache.set(self._cache_key, orders)
        LOG.info(f"Saved {len(orders)} orders to pending cache.")

    def _haversine_distance_km(self, loc1: Location, loc2: Location) -> float:
        lat1, lon1 = loc1.latitude, loc1.longitude
        lat2, lon2 = loc2.latitude, loc2.longitude
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

        c = 2 * asin(sqrt(a))
        return c * RADIUS_OF_EARTH_KM

    async def _get_Maps_travel_info(
        self, origin_loc: Location, destination_loc: Location
    ) -> dict | None:
        """
        CONCEPTUAL: Fetches travel distance and duration from Google Maps Distance Matrix API.
        Implement with `aiohttp` or an async Google Maps client here.
        """
        LOG.debug(
            f"Calling Google Maps Distance Matrix for {origin_loc} to {destination_loc}"
        )
        await asyncio.sleep(0.1)  # Simulate network delay

        distance_km = self._haversine_distance_km(origin_loc, destination_loc)
        estimated_duration_seconds = distance_km * \
            (120 / 1)  # Approx 1km in 2 minutes
        LOG.debug(
            f"Using dummy travel info (Haversine + estimation): distance={distance_km:.2f}km, duration={estimated_duration_seconds:.0f}s"
        )
        return {
            "distance_km": distance_km,
            "duration_seconds": estimated_duration_seconds,
        }

    async def _optimize_waypoints_with_Maps(
        self, raw_waypoints_data: list[dict], delivery_job_id: UUID
    ) -> tuple[list[Waypoint], float, int]:
        """
        CONCEPTUAL: Optimizes the sequence of waypoints using Google Maps Routes API.
        Implement with `aiohttp` or an async Google Maps client here.
        """
        LOG.info(
            f"Optimizing {len(raw_waypoints_data)} waypoints using Google Maps (conceptual)."
        )
        await asyncio.sleep(0.2)  # Simulate network delay

        # In a real scenario, you'd parse Google Maps Routes API response
        # to get the optimized order and actual total distance/time.
        optimized_order_indices = list(range(len(raw_waypoints_data)))
        reordered_waypoints_data = [
            raw_waypoints_data[i] for i in optimized_order_indices
        ]

        total_distance_km = 0.0
        total_time_minutes = 0

        # Simple accumulation for demonstration
        for i in range(len(reordered_waypoints_data) - 1):
            loc1 = reordered_waypoints_data[i]["location"]
            loc2 = reordered_waypoints_data[i + 1]["location"]
            segment_distance = self._haversine_distance_km(loc1, loc2)
            total_distance_km += segment_distance
            total_time_minutes += (segment_distance / 30) * 60  # Approx 30km/h
            total_time_minutes += 5  # Add 5 minutes for stop time

        if total_time_minutes < 15:
            total_time_minutes = 15

        final_waypoints: list[Waypoint] = []
        for i, wp_data in enumerate(reordered_waypoints_data):
            final_waypoints.append(
                await self._waypoint_service.create_waypoint(
                    CreateWaypointModel(
                        delivery_job_id=delivery_job_id,
                        order_id=wp_data["order_id"],
                        sequence=i,
                        expected_arrival_time=wp_data["eta"],
                        waypoint_type=wp_data["type"],
                        waypoint_status=WaypointStatus.PENDING,
                    )
                )
            )

        LOG.info(
            f"Waypoint optimization completed. Est. Distance: {total_distance_km:.2f} km, Est. Time: {total_time_minutes:.0f} min."
        )
        return final_waypoints, total_distance_km, int(total_time_minutes)
