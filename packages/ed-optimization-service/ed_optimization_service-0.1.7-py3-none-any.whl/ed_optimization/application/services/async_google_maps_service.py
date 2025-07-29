# ed_optimization/infrastructure/api/Maps_client.py

import asyncio
from datetime import datetime
from math import asin, cos, sin, sqrt
from typing import Any, Dict, Optional

from ed_domain.core.aggregate_roots import Location

from ed_optimization.common.logging_helpers import get_logger

# You'd typically install `google-maps-services-python` if you were wrapping it,
# but for a pure async approach, you'd use aiohttp.
# import googlemaps

RADIUS_OF_EARTH_KM = 6371

LOG = get_logger()


class AsyncGoogleMapsClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google Maps API key must be provided.")
        self._api_key = api_key
        # For a real implementation, you might initialize an aiohttp.ClientSession here
        # self._session = aiohttp.ClientSession()

        # If wrapping googlemaps-services-python (synchronous client)
        # self._gmaps = googlemaps.Client(key=api_key)
        LOG.info("AsyncGoogleMapsClient initialized (conceptual).")

    # In a real application, you might want to close the session on shutdown
    # async def close(self):
    #     if hasattr(self, '_session') and self._session:
    #         await self._session.close()

    async def get_distance_matrix(
        self,
        origins: list[Location],
        destinations: list[Location],
        mode: str = "driving",
        traffic_model: str = "best_guess",  # "best_guess", "optimistic", "pessimistic"
        # Used for traffic-aware routing
        departure_time: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Conceptually fetches distance and duration using Google Maps Distance Matrix API.
        In a real implementation, this would make an actual async HTTP request.
        """
        LOG.debug(
            f"Calling Google Maps Distance Matrix for origins: {origins} to destinations: {destinations}"
        )

        # --- REAL IMPLEMENTATION WITH AIOHTTP (conceptual) ---
        # base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        # params = {
        #     "origins": "|".join([f"{loc['latitude']},{loc['longitude']}" for loc in origins]),
        #     "destinations": "|".join([f"{loc['latitude']},{loc['longitude']}" for loc in destinations]),
        #     "mode": mode,
        #     "key": self._api_key,
        #     "units": "metric",
        # }
        # if departure_time:
        #     params["departure_time"] = int(departure_time.timestamp())
        #     params["traffic_model"] = traffic_model

        # try:
        #     async with self._session.get(base_url, params=params) as response:
        #         response.raise_for_status()
        #         data = await response.json()
        #         return data
        # except aiohttp.ClientError as e:
        #     LOG.error(f"Google Maps Distance Matrix API call failed: {e}")
        #     return None
        # --- END REAL IMPLEMENTATION ---

        # --- MOCK IMPLEMENTATION (for demonstration without a real API key/network) ---
        await asyncio.sleep(0.05)  # Simulate network latency

        # For simplicity, calculate Haversine for the first origin-destination pair
        if not origins or not destinations:
            return None

        loc1 = origins[0]
        loc2 = destinations[0]
        distance_km = self._haversine_distance_km(loc1, loc2)
        # Simple estimation: 1km = 2 minutes travel time in non-peak hours
        # Assume 30 km/h average speed in general (500m/min)
        estimated_duration_seconds = distance_km * \
            (120 / 1)  # 120 seconds per km

        mock_response = {
            "destination_addresses": ["Mock Destination"],
            "origin_addresses": ["Mock Origin"],
            "rows": [
                {
                    "elements": [
                        {
                            "distance": {
                                "text": f"{distance_km:.2f} km",
                                "value": int(distance_km * 1000),
                            },
                            "duration": {
                                "text": f"{estimated_duration_seconds/60:.0f} mins",
                                "value": int(estimated_duration_seconds),
                            },
                            "status": "OK",
                        }
                    ]
                }
            ],
            "status": "OK",
        }
        LOG.debug("Mock Google Maps Distance Matrix response generated.")
        return mock_response
        # --- END MOCK IMPLEMENTATION ---

    async def compute_routes(
        self,
        origin: Location,
        destination: Location,
        intermediate_waypoints: list[Location],
        travel_mode: str = "DRIVE",  # "DRIVE", "BICYCLE", "WALK", "TWO_WHEELER"
        # "TRAFFIC_AWARE_OPTIMAL", "TRAFFIC_AWARE", "UNSPECIFIED"
        routing_preference: str = "TRAFFIC_AWARE_OPTIMAL",
        optimize_waypoints: bool = True,  # Key for reordering waypoints
    ) -> Optional[Dict[str, Any]]:
        """
        Conceptually fetches an optimized route using Google Maps Routes API.
        In a real implementation, this would make an actual async HTTP request.
        """
        LOG.debug("Calling Google Maps Routes API for optimization.")

        # --- REAL IMPLEMENTATION WITH AIOHTTP (conceptual) ---
        # base_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        # headers = {"Content-Type": "application/json", "X-Goog-Api-Key": self._api_key, "X-Goog-FieldMask": "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,routes.legs.steps,routes.optimizedIntermediateWaypointIndex"}
        #
        # body = {
        #     "origin": {"location": {"latLng": {"latitude": origin["latitude"], "longitude": origin["longitude"]}}},
        #     "destination": {"location": {"latLng": {"latitude": destination["latitude"], "longitude": destination["longitude"]}}},
        #     "intermediates": [
        #         {"location": {"latLng": {"latitude": wp["latitude"], "longitude": wp["longitude"]}}}
        #         for wp in intermediate_waypoints
        #     ],
        #     "travelMode": travel_mode,
        #     "routingPreference": routing_preference,
        #     "computeAlternativeRoutes": False,
        #     "optimizeWaypointOrder": optimize_waypoints, # This is the crucial part for reordering
        #     # "departureTime": int(datetime.now(UTC).timestamp()), # For traffic predictions
        # }
        # try:
        #     async with self._session.post(base_url, headers=headers, json=body) as response:
        #         response.raise_for_status()
        #         data = await response.json()
        #         return data
        # except aiohttp.ClientError as e:
        #     LOG.error(f"Google Maps Routes API call failed: {e}")
        #     return None
        # --- END REAL IMPLEMENTATION ---

        # --- MOCK IMPLEMENTATION (for demonstration) ---
        await asyncio.sleep(0.1)  # Simulate network latency

        # For mocking, we'll just return waypoints in the order they were provided
        # The 'optimizedIntermediateWaypointIndex' would come from Google Maps
        # In this mock, we'll assign sequential indices.
        total_locations = [origin] + intermediate_waypoints + [destination]
        total_distance_meters = 0
        total_duration_seconds = 0

        for i in range(len(total_locations) - 1):
            loc1 = total_locations[i]
            loc2 = total_locations[i + 1]
            segment_distance_km = self._haversine_distance_km(loc1, loc2)
            segment_duration_seconds = segment_distance_km * 120  # 2 mins/km
            total_distance_meters += segment_distance_km * 1000
            total_duration_seconds += segment_duration_seconds

        mock_optimized_indices = list(
            range(len(intermediate_waypoints))
        )  # 0-indexed for intermediates

        mock_response = {
            "routes": [
                {
                    "distanceMeters": int(total_distance_meters),
                    "duration": f"{int(total_duration_seconds)}s",
                    "optimizedIntermediateWaypointIndex": mock_optimized_indices,
                    "polyline": {"encodedPolyline": "mock_polyline_string"},
                    "legs": [],  # Simplified for mock
                }
            ]
        }
        LOG.debug("Mock Google Maps Routes API response generated.")
        return mock_response
        # --- END MOCK IMPLEMENTATION ---

    def _haversine_distance_km(self, loc1: Location, loc2: Location) -> float:
        """Calculates the Haversine distance for internal mock use."""
        lat1, lon1 = loc1.latitude, loc1.longitude
        lat2, lon2 = loc2.latitude, loc2.longitude
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

        c = 2 * asin(sqrt(a))

        return c * RADIUS_OF_EARTH_KM
