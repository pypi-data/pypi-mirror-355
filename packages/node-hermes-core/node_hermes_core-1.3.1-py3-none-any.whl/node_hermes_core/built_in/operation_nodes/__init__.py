from .aggregator_node import AggegatorNode
from .reference_node import ReferenceWorkerNode

NODES = [AggegatorNode, ReferenceWorkerNode]

__all__ = [
    "NODES",
]
