from typing import Callable, List, Type

from ..nodes.generic_node import GenericNode
from .signal import Signal


class NodeDependencyManager:
    nodes: List["GenericNode"]
    _dependency_change_callback: List[Callable]
    dependency_change: Signal

    def __init__(self, dependency_name: str, node: Type["GenericNode"]):
        self.type = node
        self.dependency_name = dependency_name
        self.dependency_change = Signal()
        self.nodes = []

    def add_node(self, node: "GenericNode"):
        if node not in self.nodes:
            self.nodes.append(node)
            self.dependency_change.emit()

    def remove_node(self, node: "GenericNode"):
        if node in self.nodes:
            self.nodes.remove(node)
            self.dependency_change.emit()

    def get_node(self):
        """NOTE: Assumes that there is only one node"""

        assert len(self.nodes) == 1, "More than one node found"
        return self.nodes[0]
