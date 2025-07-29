from datetime import datetime
from typing import NotRequired, Optional, TypedDict
from uuid import UUID

from ed_domain.core.aggregate_roots import Location
from ed_domain.core.entities.waypoint import WaypointType


class RawWaypoint(TypedDict):
    order_id: UUID
    expected_arrival_time: datetime
    location: Location
    waypoint_type: WaypointType


class LatLng(TypedDict):
    latitude: float
    longitude: float


class XLocation(TypedDict):
    latLng: LatLng


class GoogleMapsLocation(TypedDict):
    location: XLocation


class Route(TypedDict):
    distanceMeters: float
    duration: str
    optimizedIntermediateWaypointIndex: Optional[list[int]]


class OptimizedRoute(TypedDict):
    routes: list[Route]


class OptimizedRouteInformation(TypedDict):
    distance_meters: NotRequired[float]
    duration_seconds: int
    waypoints: list[RawWaypoint]


class RouteInformation(TypedDict):
    distance_meters: NotRequired[float]
    duration_seconds: int
    waypoints: list[Location]
