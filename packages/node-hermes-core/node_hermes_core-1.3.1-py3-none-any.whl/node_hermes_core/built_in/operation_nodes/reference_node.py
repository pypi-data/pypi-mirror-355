from typing import Literal
from ...nodes import GenericNode, AbstractWorker
from ...depencency.node_dependency import NodeDependency


class ReferenceWorkerNode(GenericNode, AbstractWorker):
    class Config(GenericNode.Config):
        type: Literal["reference_worker"]
        node: str

    config: Config  # type: ignore
    reference_node: GenericNode | None = None

    def __init__(self, config: Config):
        super().__init__(config)
        # Get the reference node
        self.references_node = NodeDependency(
            name="reference_node",
            config=self.config.node,
            reference=None,
        )
        self.dependency_manager.add(self.references_node)

    def init(self, reference_node: GenericNode):  # type: ignore
        super().init()
        self.reference_node = reference_node

    def work(self):
        assert self.reference_node is not None, "Reference node is not initialized"
        assert isinstance(self.reference_node, AbstractWorker), "Reference node is not a worker node"
        self.reference_node.work()

    def deinit(self):
        self.reference_node = None
        super().deinit()
