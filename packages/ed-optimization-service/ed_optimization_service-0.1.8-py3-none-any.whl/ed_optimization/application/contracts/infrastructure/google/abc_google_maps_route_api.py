from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from ed_domain.core.aggregate_roots import Location

from ed_optimization.application.contracts.infrastructure.google.types import (
    GoogleMapsLocation, OptimizedRoute, OptimizedRouteInformation, RawWaypoint,
    RouteInformation)


class ABCGoogleMapsRoutesAPI(ABC):
    @abstractmethod
    async def optimize_routes(
        self, waypoints: list[RawWaypoint]
    ) -> Optional[OptimizedRouteInformation]: ...

    @abstractmethod
    async def get_route(
        self, origin: Location, destination: Location
    ) -> RouteInformation: ...

    @abstractmethod
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
    ) -> OptimizedRoute: ...

    def _get_Maps_location(self, location: Location) -> GoogleMapsLocation:
        return {
            "location": {
                "latLng": {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }
            }
        }

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...
