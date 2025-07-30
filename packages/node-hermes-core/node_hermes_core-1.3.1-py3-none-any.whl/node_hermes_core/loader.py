import importlib
from typing import List, Type, Dict

from .nodes import GenericNode

LOADED_NODES = []
SYSTEM_NODES: Dict[str, Type[GenericNode]] = {}


def register_node(component):
    # Check if the component is already loaded by name
    print(f"Registering component {component}")
    if component not in LOADED_NODES:
        LOADED_NODES.append(component)
    else:
        print(f"Component {component} already loaded")


def register_system_node(node):
    SYSTEM_NODES[node.__name__] = node


def register_nodes(components):
    for component in components:
        register_node(component)


def import_nodes(components: str, component_collection_name: str = "NODES"):
    loaded_components = importlib.import_module(components)

    register_nodes(getattr(loaded_components, component_collection_name))


def load_modules(components: List[str], component_collection_name: str = "NODES"):
    for component in components:
        import_nodes(component, component_collection_name)

    return LOADED_NODES


def get_class_handle(config: GenericNode.Config) -> Type[GenericNode]:
    components: list[Type[GenericNode]] = LOADED_NODES

    for component in components:
        if type(config) is component.Config:
            return component

    for node_name, node in SYSTEM_NODES.items():
        if node.Config.__qualname__ == config.__class__.__qualname__:
            return node

    raise ValueError(f"Component not found for config {config}")
