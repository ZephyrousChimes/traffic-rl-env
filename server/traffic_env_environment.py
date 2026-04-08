# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Traffic Env Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""

from uuid import uuid4
from typing import Optional, Any

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import TrafficAction, TrafficObservation, NodeType, Road, Route, Phase, Intersection, Node, RoadNetwork
except ImportError:
    from models import TrafficAction, TrafficObservation, NodeType, Road, Route, Phase, Intersection, Node, RoadNetwork


class TrafficEnvironment(Environment):
    """
    A simple echo environment that echoes back messages.

    This environment is designed for testing the HTTP server infrastructure.
    It maintains minimal state and simply echoes back whatever message it receives.

    Example:
        >>> env = TrafficEnvironment()
        >>> obs = env.reset()
        >>> print(obs.echoed_message)  # "Traffic Env environment ready!"
        >>>
        >>> obs = env.step(TrafficAction(message="Hello"))
        >>> print(obs.echoed_message)  # "Hello"
        >>> print(obs.message_length)  # 5
    """

    # Enable concurrent WebSocket sessions.
    # Set to True if your environment isolates state between instances.
    # When True, multiple WebSocket clients can connect simultaneously, each
    # getting their own environment instance (when using factory mode in app.py).
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the traffic_env environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count = 0

    def create_network(self, seed: Optional[int] = 42):
        center_node = Node(type=NodeType.JUNCTION)
        north_node = Node(type=NodeType.ENDPOINT)
        south_node = Node(type=NodeType.ENDPOINT)
        east_node  = Node(type=NodeType.ENDPOINT)
        west_node  = Node(type=NodeType.ENDPOINT)

        nc_road = Road(
            src=north_node.id,
            dst=center_node.id
        )
        cn_road = Road(
            src=center_node.id,
            dst=north_node.id
        )

        sc_road = Road(
            src=south_node.id,
            dst=center_node.id
        )
        cs_road = Road(
            src=center_node.id,
            dst=south_node.id
        )

        ec_road = Road(
            src=east_node.id,
            dst=center_node.id
        )
        ce_road = Road(
            src=center_node.id,
            dst=east_node.id
        )

        wc_road = Road(
            src=west_node.id,
            dst=center_node.id
        )
        cw_road = Road(
            src=center_node.id,
            dst=west_node.id
        )


        # Routes
        sn_route = Route(inroad=sc_road.id, outroad=cn_road.id)
        se_route = Route(inroad=sc_road.id, outroad=ce_road.id)
        sw_route = Route(inroad=sc_road.id, outroad=cw_road.id)

        ns_route = Route(inroad=nc_road.id, outroad=cs_road.id)
        ne_route = Route(inroad=nc_road.id, outroad=ce_road.id)
        nw_route = Route(inroad=nc_road.id, outroad=cw_road.id)

        en_route = Route(inroad=ec_road.id, outroad=cn_road.id)
        es_route = Route(inroad=ec_road.id, outroad=cs_road.id)
        ew_route = Route(inroad=ec_road.id, outroad=cw_road.id)

        wn_route = Route(inroad=wc_road.id, outroad=cn_road.id)
        ws_route = Route(inroad=wc_road.id, outroad=cs_road.id)
        we_route = Route(inroad=wc_road.id, outroad=ce_road.id)


        unregulated_phase = Phase(routes=[])

        phase_set = [
            Phase(routes=[
                sw_route.id, wn_route.id, ne_route.id, es_route.id,
                ns_route.id, nw_route.id,
            ]),

            Phase(routes=[
                sw_route.id, wn_route.id, ne_route.id, es_route.id,
                sn_route.id, se_route.id,
            ]),

            Phase(routes=[
                sw_route.id, wn_route.id, ne_route.id, es_route.id,
                en_route.id, ew_route.id,
            ]),

            Phase(routes=[
                sw_route.id, wn_route.id, ne_route.id, es_route.id,
                ws_route.id, we_route.id,
            ]),
        ]


        nodes = [
            center_node,
            north_node,
            south_node,
            east_node,
            west_node
        ]

        roads = [
            nc_road, cn_road,
            sc_road, cs_road,
            ec_road, ce_road,
            wc_road, cw_road
        ]

        routes = [
            ns_route, ne_route, nw_route,
            sn_route, se_route, sw_route,
            en_route, es_route, ew_route,
            wn_route, ws_route, we_route,
        ]

        intersections = [
            Intersection(
                node = center_node.id,
                routes = routes,
                phase_set=phase_set,
                phase = unregulated_phase.id
            )
        ]

        self.road_network = RoadNetwork(
            nodes=nodes,
            roads=roads,
            intersections=intersections
        )


    def initiate_traffic(self, seed: Optional[int] = 42):
        pass

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> TrafficObservation:
        """
        Reset the environment.

        Returns:
            TrafficObservation with a ready message
        """
        
        road_network = self.road_network
        return TrafficObservation(
            road_network=self.road_network,
            done=False,
            reward=0.0,
        )

    def step(self, action: TrafficAction) -> TrafficObservation:  # type: ignore[override]
        """
        Execute a step in the environment by echoing the message.

        Args:
            action: TrafficAction containing the message to echo

        Returns:
            TrafficObservation with the echoed message and its length
        """
        self._state.step_count += 1

        message = action.message
        length = len(message)

        # Simple reward: longer messages get higher rewards
        reward = length * 0.1

        return TrafficObservation(
            road_network=self.road_network,
            done=False,
            reward=reward,
            metadata={"original_message": message, "step": self._state.step_count},
        )

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state


'''
First reward model should be about correctness. So, no accidents. No available intersection gone without signal.

Second reward metric is about reducing the p95. So, we just plainly take the inverse of the p95.

Third reward metric is the priority vehicle. The wait time of the priority vehicle will degrade the reward very aggressively.
'''

'''
The environment reset:

We create a new road network. We use a seeded rng to fill
in vehicles in each road.
The order should look something like this, we do top down-

First create a single node.
For that create four roads.
Then give the roads to node.

Create an intersection and give it the roads.
Then define the valid phases.
Reset all phases.

Then we populate the roads with vehicle list.

Then give the intersection to the node.
'''

'''
The environment step:

Every action includes phase declaration for each intersection. 

First validate. If there are any invalid phases, give a reward of 0 with the error point.

Roads headed to endpoints must be cleared of their lists first.
Second, move the wait lists. Just empty it from one road object to another. Keep it simple for now. If you want, a little randomness adding or subtracting stuff. Power law if you want. Actually I think it will be Poisson addition... and subtraction. See queue theory.
Then move the current wait
Remove the old wait lists.

Third, give the state back. Done.
'''