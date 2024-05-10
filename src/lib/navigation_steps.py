from dataclasses import dataclass
from src.core.custom_types import Seconds_t
from src.lib.navigation_graph import TransitNetworkNode
from typing import Optional


@dataclass
class NavStep:
    """What does it take to get to a node? (graph edge) E.G. Take the 123 Bus line or Walk 20 minutes"""
    start_node: Optional[TransitNetworkNode]
    destination_node: Optional[TransitNetworkNode]
    time_start: Seconds_t
    time_end: Seconds_t


@dataclass
class TakeTransit(NavStep):
    """A path between 2 TransitStopNavNodes, traversed with a transit line"""
    line_variant: str

    def __str__(self):
        return f"Take transit line {self.line_variant} {self.start_node} -> {self.destination_node}"


@dataclass
class GoOnFoot(NavStep):
    def __str__(self):
        return f"Walk from {self.start_node} to {self.destination_node}"


class StartAtNode(NavStep):
    def __init__(self, where: TransitNetworkNode, time: Seconds_t):
        super().__init__(None, where, time, time)
