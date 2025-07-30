import time
from typing import Dict, Literal

from node_hermes_core.loader import get_class_handle
from node_hermes_core.nodes.data_generator_node import AbstractWorker
from node_hermes_core.nodes.generic_node import GenericNode
from pydantic import Field, model_validator

from ..loader import register_system_node
from ..objs.managed_task import ManagedTask
from ..utils.frequency_counter import FrequencyCounter, Timer


class GenericNestedNode(GenericNode):
    class Config(GenericNode.Config):
        nodes: Dict[str, "GenericNode.Config|GenericNestedNode.Config"] = {}

        # Validater to populate the names
        @model_validator(mode="after")  # type: ignore
        def populate_names(cls, values: "GenericNestedNode.Config"):
            for node_name in values.nodes:
                values.nodes[node_name].name = node_name
            return values

    config: Config

    def __init__(self, config: Config):
        super().__init__(config)

        # Initialize all the child nodes
        for node_name, node_config in config.nodes.items():
            self.managed_child_nodes[node_name] = get_class_handle(node_config)(node_config)

    @property
    def info_string(self) -> str:
        return "werwr"


class RootNode(GenericNestedNode):
    class Config(GenericNestedNode.Config):
        type: Literal["root"]

    config: Config | GenericNestedNode.Config

    def __init__(self, config):
        super().__init__(config)
        self.name = "Root Node"
        self.link_dependencies(root_node=self)
        self.link_connections(root_node=self)


class WorkerNode(GenericNestedNode):
    class Config(GenericNestedNode.Config):
        type: Literal["worker"]
        interval: float | None = Field(description="The interval at which the worker node should work", default=1)

    config: Config | GenericNestedNode.Config

    def __init__(self, config):
        super().__init__(config)
        self.task = ManagedTask(self.process_task, f"{self.name}_process_task")
        self.task.stopped.connect(self.attempt_deinit)
        self.frequency_counter = FrequencyCounter()
        self.timer = Timer()

    @property
    def info_string(self) -> str:
        return f"{self.frequency_counter.frequency:.2f} Hz runtime {self.timer.average_runtime * 1000:.2f} ms"

    def init(self):
        super().init()

        for node in self.managed_child_nodes.values():
            assert isinstance(node, AbstractWorker), "Worker node can only have worker nodes as children"

        self.task.start()

    def deinit(self, timeout: int | None = None):
        self.task.stop(timeout)
        super().deinit()

    def process_task(self):
        assert isinstance(self.config, WorkerNode.Config), "Worker node config should be of type WorkerNode.Config"

        while True:
            if self.task.kill_signal:
                break

            self.frequency_counter.update(1)
            self.timer.start()
            # For all the child nodes do work
            for node in self.managed_child_nodes.values():
                assert isinstance(node, AbstractWorker), "Worker node can only have worker nodes as children"
                try:
                    if not not node.is_active():
                        node.work()

                except Exception:
                    self.log.exception("work failed")
                    node.attempt_deinit(True)

            self.timer.stop()
            if self.config.interval is not None:
                time.sleep(self.config.interval)


class GroupNode(GenericNestedNode, AbstractWorker):
    class Config(GenericNestedNode.Config):
        type: Literal["group"]

    config: Config | GenericNestedNode.Config

    def __init__(self, config):
        super().__init__(config)

    def work(self):
        for node in self.managed_child_nodes.values():
            assert isinstance(node, AbstractWorker), "Group node can only have worker nodes as children"
            node.work()


register_system_node(GroupNode)
register_system_node(WorkerNode)
