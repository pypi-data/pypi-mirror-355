import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

LOG = logging.getLogger(__name__)


@dataclass
class VRPLocation:
    """Represents a location in the VRP problem."""

    id: str
    latitude: float
    longitude: float
    address: str


@dataclass
class VRPOrder:
    """Represents an order in the VRP problem."""

    id: str
    pickup_location: VRPLocation
    delivery_location: VRPLocation
    pickup_time_window: Tuple[
        int, int
    ]  # (start_time, end_time) in minutes from start of day
    delivery_time_window: Tuple[int, int]
    demand: int  # weight or volume
    priority: int = 1  # higher number = higher priority


@dataclass
class VRPVehicle:
    """Represents a vehicle in the VRP problem."""

    id: str
    capacity: int
    start_location: VRPLocation
    # If None, same as start_location
    end_location: Optional[VRPLocation] = None


@dataclass
class VRPSolution:
    """Represents a solution to the VRP problem."""

    # List of routes, each route is a list of location indices
    routes: List[List[int]]
    total_distance: float
    total_time: int
    vehicle_assignments: Dict[int, str]  # vehicle_index -> vehicle_id


class ORToolsVRPSolver:
    """VRP Solver using Google OR-Tools."""

    def __init__(self):
        self.distance_matrix = None
        self.time_matrix = None
        self.locations = []
        self.orders = []
        self.vehicles = []

    def solve(
        self,
        orders: List[VRPOrder],
        vehicles: List[VRPVehicle],
        distance_matrix: np.ndarray,
        time_matrix: Optional[np.ndarray] = None,
    ) -> Optional[VRPSolution]:
        """
        Solve the VRP problem.

        Args:
            orders: List of orders to be delivered
            vehicles: List of available vehicles
            distance_matrix: Matrix of distances between all locations
            time_matrix: Matrix of travel times between all locations (optional)

        Returns:
            VRPSolution if a solution is found, None otherwise
        """
        self.orders = orders
        self.vehicles = vehicles
        self.distance_matrix = distance_matrix
        self.time_matrix = time_matrix if time_matrix is not None else distance_matrix

        # Build locations list: depot + pickup locations + delivery locations
        self._build_locations()

        # Create the routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(self.locations), len(self.vehicles), self._get_depot_indices()
        )

        # Create Routing Model
        routing = pywrapcp.RoutingModel(manager)

        # Create and register distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(self.distance_matrix[from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(
            distance_callback)

        # Define cost of each arc
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add capacity constraint
        self._add_capacity_constraint(routing, manager)

        # Add time window constraints
        self._add_time_window_constraints(routing, manager)

        # Add pickup and delivery constraints
        self._add_pickup_delivery_constraints(routing, manager)

        # Setting first solution heuristic
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.FromSeconds(30)  # 30 second time limit

        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            return self._extract_solution(manager, routing, solution)
        else:
            LOG.warning("No solution found for VRP problem")
            return None

    def _build_locations(self):
        """Build the locations list from orders and vehicles."""
        self.locations = []

        # Add depot locations (vehicle start locations)
        depot_locations = set()
        for vehicle in self.vehicles:
            depot_key = (
                vehicle.start_location.latitude,
                vehicle.start_location.longitude,
            )
            if depot_key not in depot_locations:
                self.locations.append(vehicle.start_location)
                depot_locations.add(depot_key)

        # Add pickup and delivery locations
        for order in self.orders:
            self.locations.append(order.pickup_location)
            self.locations.append(order.delivery_location)

    def _get_depot_indices(self) -> List[int]:
        """Get the indices of depot locations."""
        # For simplicity, assume all vehicles start from the same depot (index 0)
        return [0] * len(self.vehicles)

    def _add_capacity_constraint(self, routing, manager):
        """Add vehicle capacity constraints."""

        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            # Depot has 0 demand, pickup locations have positive demand, delivery locations have negative demand
            if from_node == 0:  # Depot
                return 0

            # Find which order this location belongs to
            location_index = from_node - 1  # Subtract 1 for depot
            if location_index < len(self.orders):  # Pickup location
                return self.orders[location_index].demand
            else:  # Delivery location
                order_index = location_index - len(self.orders)
                return -self.orders[order_index].demand

        demand_callback_index = routing.RegisterUnaryTransitCallback(
            demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            [
                vehicle.capacity for vehicle in self.vehicles
            ],  # vehicle maximum capacities
            True,  # start cumul to zero
            "Capacity",
        )

    def _add_time_window_constraints(self, routing, manager):
        """Add time window constraints."""

        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(self.time_matrix[from_node][to_node])

        time_callback_index = routing.RegisterTransitCallback(time_callback)

        # Create time dimension
        routing.AddDimension(
            time_callback_index,
            30,  # allow waiting time
            1440,  # maximum time per vehicle (24 hours in minutes)
            False,  # Don't force start cumul to zero
            "Time",
        )
        time_dimension = routing.GetDimensionOrDie("Time")

        # Add time window constraints for each location
        for location_idx, location in enumerate(self.locations):
            if location_idx == 0:  # Depot
                time_dimension.CumulVar(manager.NodeToIndex(location_idx)).SetRange(
                    0, 1440
                )
            else:
                # Find the corresponding order and whether this is pickup or delivery
                order_idx, is_pickup = self._get_order_info_for_location(
                    location_idx)
                if order_idx is not None:
                    order = self.orders[order_idx]
                    time_window = (
                        order.pickup_time_window
                        if is_pickup
                        else order.delivery_time_window
                    )
                    time_dimension.CumulVar(manager.NodeToIndex(location_idx)).SetRange(
                        time_window[0], time_window[1]
                    )

    def _add_pickup_delivery_constraints(self, routing, manager):
        """Add pickup and delivery constraints."""
        for order_idx, order in enumerate(self.orders):
            pickup_index = manager.NodeToIndex(1 + order_idx)  # +1 for depot
            delivery_index = manager.NodeToIndex(
                1 + len(self.orders) + order_idx)
            routing.AddPickupAndDelivery(pickup_index, delivery_index)
            routing.solver().Add(
                routing.VehicleVar(
                    pickup_index) == routing.VehicleVar(delivery_index)
            )
            routing.solver().Add(
                routing.CumulVar(pickup_index, "Time")
                <= routing.CumulVar(delivery_index, "Time")
            )

    def _get_order_info_for_location(
        self, location_idx: int
    ) -> Tuple[Optional[int], bool]:
        """Get order index and whether location is pickup for a given location index."""
        if location_idx == 0:  # Depot
            return None, False

        adjusted_idx = location_idx - 1  # Subtract 1 for depot
        if adjusted_idx < len(self.orders):  # Pickup location
            return adjusted_idx, True
        else:  # Delivery location
            return adjusted_idx - len(self.orders), False

    def _extract_solution(self, manager, routing, solution) -> VRPSolution:
        """Extract the solution from OR-Tools solution object."""
        routes = []
        vehicle_assignments = {}
        total_distance = 0
        total_time = 0

        for vehicle_id in range(len(self.vehicles)):
            route = []
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_time = 0

            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route.append(node_index)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )

            route.append(manager.IndexToNode(index))  # Add the end depot
            routes.append(route)
            vehicle_assignments[vehicle_id] = self.vehicles[vehicle_id].id
            total_distance += route_distance

            # Calculate route time
            time_dimension = routing.GetDimensionOrDie("Time")
            route_time = solution.Value(
                time_dimension.CumulVar(routing.End(vehicle_id))
            )
            total_time = max(total_time, route_time)

        return VRPSolution(
            routes=routes,
            total_distance=total_distance,
            total_time=total_time,
            vehicle_assignments=vehicle_assignments,
        )
