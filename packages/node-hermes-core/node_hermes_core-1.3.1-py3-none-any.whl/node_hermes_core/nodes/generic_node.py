import logging
import random
from enum import Enum
from typing import Awaitable, Dict, List, Union

from node_hermes_core.depencency.node_dependency import RootNodeDependency
from node_hermes_core.links.queued_link import QueuedLink
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from ..depencency import NodeDependency
from ..links import DataTarget, GenericLink
import asyncio
from abc import ABC, abstractmethod


class SinkPortManager:
    links: Dict[str, GenericLink]

    def __init__(self):
        self.links = {}

    def add(self, name: str, target: GenericLink):
        self.links[name] = target


class SourcePortManager:
    targets: Dict[str, DataTarget]

    def __init__(self):
        self.targets = {}

    def add(self, name: str, target: DataTarget):
        self.targets[name] = target


class DependencyManager:
    dependencies: List[NodeDependency | RootNodeDependency]

    def __init__(self, parent: "GenericNode"):
        self.parent = parent
        self.dependencies = []

    def add(self, dependency: NodeDependency | RootNodeDependency):
        self.dependencies.append(dependency)

        # Initalize child nodes specified as dependency
        if isinstance(dependency, NodeDependency):
            if isinstance(dependency.config, GenericNode.Config):
                # Get the class from the config
                from node_hermes_core.loader import get_class_handle

                self.parent.managed_child_nodes[dependency.name] = get_class_handle(dependency.config)(  # type: ignore
                    dependency.config  # type: ignore
                )


class GenericNode():
    """Generic component class that can be used to create a component"""

    class State(Enum):
        IDLE = -1  # Idle state
        INITIALIZING = 0  # Initialising, but not yet started
        ACTIVE = 1  # Running
        DEINITIALISING = 5  # Deinitialising
        STOPPED = 2  # Stopped on request
        ERROR = 3  # Error state

        sink_port_manager: SinkPortManager

    source_port_manager: SourcePortManager
    dependency_manager: DependencyManager
    managed_child_nodes: Dict[str, "GenericNode"]

    class Config(BaseModel):
        class ManagementConfig(BaseModel):
            auto_start: bool = Field(
                default=True, description="If the node should start automatically, when the system starts"
            )
            auto_restart: bool = Field(default=False, description="If the node should restart automatically")

        model_config = ConfigDict(extra="forbid")  # Don't allow extra fields

        management: ManagementConfig = Field(default_factory=ManagementConfig, description="Management settings")

        # The name of the device
        _device_name: str = PrivateAttr(default=None)  # type: ignore

        # Reference to the component instance which was created from this config
        _component_instance: "GenericNode" = PrivateAttr(default=None)  # type: ignore

        @property
        def name(self):
            return self._device_name

        @name.setter
        def name(self, value):
            self._device_name = value

        @classmethod
        def default(cls) -> "GenericNode.Config":
            raise NotImplementedError(f"Default method not implemented for {cls.__name__}")

    _state: State = State.IDLE
    log: logging.Logger

    def __init__(self, config: Config | None) -> None:
        # If no config is provided, use the default config
        if config is None:
            config = self.Config.default()

        # If the device name is not set, generate one
        if not config._device_name:
            config._device_name = f"{self.__class__.__name__}_{random.randint(0, 1000)}"

        # Set the config
        self.config = config

        # Dependency managers
        self.sink_port_manager = SinkPortManager()
        self.source_port_manager = SourcePortManager()
        self.dependency_manager = DependencyManager(self)
        self.managed_child_nodes = {}

        self.log = logging.getLogger(f"{self.__class__.__name__}[{self.config._device_name}]")
        self.log.info("Initialised")

    @property
    def info_string(self) -> str:
        return "not defined"

    @property
    def queue_string(self) -> str:
        return "not defined"

    def link_dependencies(self, root_node: "GenericNode"):
        """
        Link the dependencies of the component, to make sure that
        the dependencies are available when the component is initialized
        """
        self.log.info("Linking dependencies")

        # Link dependencies
        for dependency in self.dependency_manager.dependencies:
            if isinstance(dependency, NodeDependency):
                if isinstance(dependency.config, GenericNode.Config):
                    assert dependency.name in self.managed_child_nodes, (
                        f"Node {dependency.name} not found in child nodes"
                    )
                    node = self.managed_child_nodes[dependency.name]
                    dependency.add_node(node)

                elif isinstance(dependency.config, str):
                    nodes = root_node.find_node(self, root_node, dependency.config)
                    assert len(nodes) == 1, f"More than one node found for {dependency.config}"
                    dependency.add_node(nodes[0])

            elif isinstance(dependency, RootNodeDependency):
                dependency.set_node(root_node)

        # Link all the child nodes
        for node in self.managed_child_nodes.values():
            node.link_dependencies(root_node)

    def link_connections(self, root_node: "GenericNode"):
        """
        Link the connection of the component, to make sure that
        the dependencies are available when the component is initialized
        """
        self.log.info("Linking connections")

        # Link dependencies
        for link_name, link in self.sink_port_manager.links.items():
            assert isinstance(link, QueuedLink)
            for node_name in link.config.nodes:
                nodes = root_node.find_node(self, root_node, node_name)
                for node in nodes:
                    assert "output" in node.source_port_manager.targets, f"Node {node} does not have an output port"
                    node.source_port_manager.targets["output"].add_target(link)

        for node in self.managed_child_nodes.values():
            node.link_connections(root_node)

    def get_child_nodes(self, recursive: bool) -> List["GenericNode"]:
        """Get all the child nodes of the component"""
        nodes = []
        for name, node in self.managed_child_nodes.items():
            nodes.append(node)
            if recursive:
                nodes.extend(node.get_child_nodes(recursive=recursive))

        return nodes

    def find_node(self, start_node: "GenericNode", root_node: "GenericNode", name: str) -> List["GenericNode"]:
        """Find a node by name, of multiple nodes if a group is specified

        Example inputs:
        - inputs.* (selecting a group)
        - inputs.input1 (selecting a single node)
        - inputs.input1.* (selecting a group within a group)
        - inputs.** (selecting all nodes recursively)
        - inputs.input1.** (selecting all nodes recursively from a single node)

        """

        # Split the name
        parts = name.split(".")

        # If the name is a single node
        if len(parts) == 1:
            if parts[0] == "*":
                return self.get_child_nodes(recursive=False)

            elif parts[0] == "**":
                return self.get_child_nodes(recursive=True)

            elif name in self.managed_child_nodes:
                return [self.managed_child_nodes[name]]
            else:
                raise ValueError(f"Node {name} not found,specified as a depencency in {self.name}")

        else:
            if parts[0] not in self.managed_child_nodes:
                raise ValueError(f"Node {parts[0]} not found")

            node = self.managed_child_nodes[parts[0]]
            return node.find_node(start_node, root_node, ".".join(parts[1:]))

    @property
    def name(self):
        return self.config._device_name

    @name.setter
    def name(self, value):
        self.config._device_name = value

    @property
    def state(self) -> "GenericNode.State":
        return self._state

    @state.setter
    def state(self, value: "GenericNode.State"):
        if self.log:
            self.log.debug(f"{self.name} state changed {self._state.name} -> {value.name}")
        self._state = value

    def is_active(self):
        return self.state == self.State.ACTIVE

    def __str__(self):
        return f"{self.__class__.__name__}[{self.name}]"

    def monitor_node_state(self, node: "GenericNode"):
        if not node.is_active():
            self.log.warning(f"Node is not active, turning off, node {node}, state {node.state}")
            self.deinit()

    def collect_depependencies(self) -> dict:
        deps = {}
        for dep in self.dependency_manager.dependencies:
            deps[dep.name] = dep.get_dependency()
        return deps

    def recursive_deinit(self, timeout: int | None = None):
        for node in self.managed_child_nodes.values():
            node.recursive_deinit(timeout=timeout)

        self.attempt_deinit()

    def get_flat_node_list(self, path: str = "") -> List["GenericNode"]:
        nodes = []
        nodes.append(self)
        for node in self.managed_child_nodes.values():
            nodes.extend(node.get_flat_node_list(path=path + f"{node.name}."))
        return nodes

    def init(self) -> Awaitable[None] | None:
        """Initializes the component"""
        pass

    def deinit(self) -> Awaitable[None] | None:
        """Deinitializes the component"""
        pass

    def attempt_init(self, **kwargs) -> Union[None, Awaitable[None]]:
        # If already active, return
        if self.is_active():
            return

        # Initialize all the managed child nodes
        for node in self.managed_child_nodes.values():
            if not node.config.management.auto_start:
                continue

            if isinstance(node, AsyncGenericNode):
                asyncio.create_task(node.attempt_init(**kwargs))
            else:
                node.attempt_init(**kwargs)

        # Derive all the dependencies
        deps = self.collect_depependencies()

        # Initialize the dependency and its children
        for dep in deps:
            node = deps[dep]

            if isinstance(node, GenericNode):
                # TODO: fix this
                if node.name == "Root Node":
                    continue

                if not node.config.management.auto_start:
                    continue

                if isinstance(node, AsyncGenericNode):
                    asyncio.create_task(node.attempt_init(**kwargs))
                else:
                    node.attempt_init(**kwargs)

        try:
            self.state = self.State.INITIALIZING
            self.init(**deps)
            self.state = self.State.ACTIVE

        except Exception:
            self.log.exception("Error initializing component")
            self.attempt_deinit(error=True)
            self.state = self.State.ERROR

    def attempt_deinit(self, error=False) -> Union[None, Awaitable[None]]:
        try:
            self.state = self.State.DEINITIALISING
            self.deinit()
            self.state = self.State.STOPPED

        except Exception as e:
            self.log.exception("Error deinitializing component")
            self.state = self.State.ERROR
            raise e

        if error:
            error = False


class AsyncGenericNode(GenericNode):
    async def init(self) -> None:
        """Initializes the component"""
        pass

    async def deinit(self) -> None:
        """Deinitializes the component"""
        pass

    async def attempt_init(self, **kwargs):
        # If already active, return
        if self.is_active():
            return

        # Initialize all the managed child nodes
        for node in self.managed_child_nodes.values():
            if not node.config.management.auto_start:
                continue

            if not isinstance(node, AsyncGenericNode):
                node.attempt_init(**kwargs)
            else:
                await node.attempt_init(**kwargs)

        # Derive all the dependencies
        deps = self.collect_depependencies()

        # Initialize the dependency
        for dep in deps:
            node = deps[dep]
            if isinstance(node, GenericNode):
                if not node.config.management.auto_start:
                    continue

                if not isinstance(node, AsyncGenericNode):
                    node.attempt_init(**kwargs)
                else:
                    await node.attempt_init(**kwargs)

        try:
            self.state = self.State.INITIALIZING
            await self.init(**deps)
            self.state = self.State.ACTIVE

        except Exception as e:
            self.log.exception("Error initializing component")
            await self.attempt_deinit(error=True)
            self.state = self.State.ERROR

    async def attempt_deinit(self, error=False):
        try:
            self.state = self.State.DEINITIALISING
            await self.deinit()
            self.state = self.State.STOPPED

        except Exception as e:
            self.log.exception("Error deinitializing component")
            self.state = self.State.ERROR
            raise e

        if error:
            error = False
