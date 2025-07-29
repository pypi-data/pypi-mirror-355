from datetime import datetime
from typing import Any, Optional

import httpx
from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Location

from ed_optimization.application.contracts.infrastructure.google.abc_google_maps_route_api import (
    ABCGoogleMapsRoutesAPI, GoogleMapsLocation, OptimizedRoute)
from ed_optimization.application.contracts.infrastructure.google.types import (
    OptimizedRouteInformation, RawWaypoint, RouteInformation)

LOG = get_logger()


class GoogleMapsRoutesAPI(ABCGoogleMapsRoutesAPI):
    COMPUTE_ROUTES_BASE_URL = (
        "https://routes.googleapis.com/directions/v2:computeRoutes"
    )

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient()

    async def optimize_routes(
        self, waypoints: list[RawWaypoint]
    ) -> Optional[OptimizedRouteInformation]:
        if len(waypoints) < 2:
            return

        origin, destination = waypoints[0], waypoints[1]
        intermediates = waypoints[2:]

        Maps_origin = self._get_Maps_location(origin["location"])
        Maps_destination = self._get_Maps_location(destination["location"])
        Maps_intermediates = [
            self._get_Maps_location(inter["location"]) for inter in intermediates
        ]

        optimized_route: OptimizedRoute = await self._compute_routes(
            Maps_origin,
            Maps_destination,
            Maps_intermediates,
            optimize_waypoint_order=True,
        )

        optimized_intermediate_indices = optimized_route["routes"][0].get(
            "optimizedIntermediateWaypointIndex"
        )

        if optimized_intermediate_indices:
            optimized_intermediates = [
                intermediates[i] for i in optimized_intermediate_indices
            ]
            waypoints = [origin] + optimized_intermediates + [destination]

        route = optimized_route["routes"][0]
        route_information: OptimizedRouteInformation = {
            "duration_seconds": int(route["duration"][:-1]),
            "waypoints": waypoints,
        }

        if "distanceMeters" in route:
            route_information["distance_meters"] = route["distanceMeters"]

        return route_information

    async def get_route(
        self, origin: Location, destination: Location
    ) -> RouteInformation:
        optimized_route = await self._compute_routes(
            self._get_Maps_location(origin),
            self._get_Maps_location(destination),
            [],
        )
        LOG.info(f"Got optimized route: {optimized_route}")
        route = optimized_route["routes"][0]

        route_information: RouteInformation = {
            "duration_seconds": int(route["duration"][:-1]),
            "waypoints": [origin, destination],
        }

        if "distanceMeters" in route:
            route_information["distance_meters"] = route["distanceMeters"]

        return route_information

    async def _compute_routes(
        self,
        origin: GoogleMapsLocation,
        destination: GoogleMapsLocation,
        intermediates: list[GoogleMapsLocation],
        travel_mode: str = "DRIVE",
        routing_preference: Optional[str] = "TRAFFIC_AWARE",
        departure_time: Optional[datetime] = None,
        arrival_time: Optional[datetime] = None,
        language_code: Optional[str] = None,
        region_code: Optional[str] = None,
        units: Optional[str] = None,
        optimize_waypoint_order: bool = True,
        extra_computations: Optional[list[str]] = None,
        traffic_model: Optional[str] = None,
        transit_preferences: Optional[dict[str, Any]] = None,
        field_mask: str = "routes.duration,routes.distanceMeters,routes.optimizedIntermediateWaypointIndex",
    ) -> OptimizedRoute:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask,
        }

        request_body = {
            "origin": origin,
            "destination": destination,
            "travelMode": travel_mode,
        }

        if intermediates:
            request_body["intermediates"] = intermediates
        if routing_preference:
            request_body["routingPreference"] = routing_preference
        if departure_time:
            request_body["departureTime"] = departure_time.isoformat() + "Z"
        if arrival_time:
            request_body["arrivalTime"] = arrival_time.isoformat() + "Z"
        if language_code:
            request_body["languageCode"] = language_code
        if region_code:
            request_body["regionCode"] = region_code
        if units:
            request_body["units"] = units
        if optimize_waypoint_order:
            request_body["optimizeWaypointOrder"] = optimize_waypoint_order
        if extra_computations:
            request_body["extraComputations"] = extra_computations
        if traffic_model:
            request_body["trafficModel"] = traffic_model
        if transit_preferences:
            request_body["transitPreferences"] = transit_preferences

        response = await self._send_request(
            self.COMPUTE_ROUTES_BASE_URL, headers, request_body
        )

        return response

    async def _send_request(self, url, headers, json) -> Any:
        try:
            response = await self.client.post(url, headers=headers, json=json)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except httpx.HTTPStatusError as e:
            print(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}: {e}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
