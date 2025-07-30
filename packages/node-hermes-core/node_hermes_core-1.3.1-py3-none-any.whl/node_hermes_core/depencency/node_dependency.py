from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from ..nodes.generic_node import GenericNode

import logging
from typing import List


class NodeDependency:
    nodes: "List[GenericNode]"

    def __init__(self, name: str, config: "GenericNode.Config | str | None", reference: "Type|None"):
        self.name = name
        self.config = config
        self.ref = reference
        self.nodes = []

    def add_node(self, node: "GenericNode"):
        logging.info(f"Adding '{node}'as dependency for '{self.name}'")
        if len(self.nodes) > 0:
            raise ValueError("Node already added")

        if node not in self.nodes:
            if self.ref is not None and not isinstance(node, self.ref):
                raise ValueError(f"Node {node} is not of type {self.ref}")
            self.nodes.append(node)
            # self.dependency_change.emit()
            
    def remove_node(self, node: "GenericNode"):
        logging.info(f"Removing '{node}'as dependency for '{self.name}'")
        if node in self.nodes:
            self.nodes.remove(node)
            # self.dependency_change.emit()

    def get_dependency(self):
        assert len(self.nodes) != 0, f"No nodes found for dependency {self.name}"
        assert len(self.nodes) == 1, "More than one node found"
        return self.nodes[0]


class RootNodeDependency:
    node: "GenericNode|None" = None

    def __init__(self, name: str):
        self.name = name
        self.node = None

    def set_node(self, node: "GenericNode"):
        self.node = node

    def get_dependency(self) -> "GenericNode":
        assert self.node is not None, f"No nodes found for dependency {self.name}"
        return self.node
