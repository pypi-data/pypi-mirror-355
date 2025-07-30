import json
from typing import Annotated, Dict, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, create_model

from node_hermes_core.loader import load_modules
from node_hermes_core.nodes.depedency import HermesDependencies
from node_hermes_core.nodes.generic_node import GenericNode
from node_hermes_core.nodes.root_nodes import GroupNode, RootNode, WorkerNode


class HermesConfigLoader:
    config: RootNode.Config

    def __init__(self, config: RootNode.Config, model: BaseModel):
        self.config = config
        self.model = model

    @classmethod
    def load_from_yaml(cls, path: str):
        # Load the required modules in order to be able to parse the full configuration
        modules = HermesDependencies.import_from_yaml(path)

        # Create the ConfigModel
        models = HermesConfigLoader.get_config_model(modules)

        # Parse the ConfigModel
        model = models["LocalHermesConfig"].from_yaml(path) # type: ignore

        # Convert into regular model
        regular_model = HermesConfigLoader.regularise_node(model, models) # type: ignore

        assert isinstance(regular_model, RootNode.Config), (
            f"Root node should be of type GroupNode, got {type(regular_model)}"
        )

        # Convert the model into a generic node
        return cls(
            config=regular_model,
            model=models["LocalHermesConfig"], # type: ignore
        )

    @staticmethod
    def regularise_node(source_node: GenericNode.Config, models):
        if isinstance(source_node, models["LocalHermesConfig"]):
            nodes = {}
            for node_name, node_config in source_node.nodes.items():  # type: ignore
                nodes[node_name] = HermesConfigLoader.regularise_node(node_config, models)
            return RootNode.Config(type="root", nodes=nodes)

        elif isinstance(source_node, models["LocalWorkerNodeConfig"]):
            nodes = {}
            for node_name, node_config in source_node.nodes.items():  # type: ignore
                nodes[node_name] = HermesConfigLoader.regularise_node(node_config, models)

            return WorkerNode.Config(type="worker", interval=source_node.interval, nodes=nodes)  # type: ignore

        elif isinstance(source_node, models["LocalGroupNodeConfig"]):
            nodes = {}
            for node_name, node_config in source_node.nodes.items():  # type: ignore
                nodes[node_name] = HermesConfigLoader.regularise_node(node_config, models)

            return GroupNode.Config(type="group", nodes=nodes)

        return source_node

    def get_root_node(self):
        return RootNode(self.config)

    def get_schema(self):
        return json.dumps(self.model.model_json_schema(), indent=2)

    @staticmethod
    def get_config_model_from_packages(packages):
        modules = load_modules(packages)
        print("Loaded modules:")
        
        for module in modules:
            print(f" - {module.__name__}")
        
        return HermesConfigLoader.get_config_model(modules)
                                    
    @staticmethod
    def get_config_model(modules) -> Dict[str, type[HermesDependencies] | type[BaseModel]]:
        # Define dynamic ComponentConfigType based on imported modules
        ComponentConfigType = Union[tuple(cls.Config for cls in modules)]  # type: ignore

        # Define ComponentsDefinition type alias
        ComponentsDefinition = Annotated[
            Union["ComponentConfigType", "LocalGroupNodeConfig", "LocalWorkerNodeConfig"],
            Field(description="Mapping of node names to device configurations", discriminator="type"),
        ]  # type: ignore

        # Dynamically create the GenericNestedConfig model
        GenericNestedConfig = create_model(
            "GenericNestedConfig",
            nodes=(Dict[str, ComponentsDefinition], {}),
            __base__=BaseModel,
            __validators__={
                # "populate_names": model_validator(mode="after")(lambda cls, values: _populate_names(values)),
            },
        )

        # Dynamically create the WorkerNodeConfig model
        LocalWorkerNodeConfig = create_model(
            "LocalWorkerNodeConfig",
            type=(Literal["worker"], ...),
            interval=(float, Field(description="The interval at which the worker node should work", default=1)),
            __base__=GenericNestedConfig,
        )

        # Dynamically create the GroupNodeConfig model
        LocalGroupNodeConfig = create_model(
            "LocalGroupNodeConfig",
            type=(Literal["group"], ...),
            __base__=GenericNestedConfig,
        )

        # Dynamically create the HermesConfig model
        LocalHermesConfig = create_model(
            "LocalHermesConfig",
            model_config=(ConfigDict, dict(extra="forbid")),
            nodes=(Dict[str, ComponentsDefinition], dict(default_factory=dict)),
            __base__=HermesDependencies,
        )

        ComponentConfigType = Union[tuple(cls.Config for cls in modules)]  # type: ignore
        LocalHermesConfig.model_rebuild()

        return {
            "LocalHermesConfig": LocalHermesConfig,
            "LocalWorkerNodeConfig": LocalWorkerNodeConfig,
            "LocalGroupNodeConfig": LocalGroupNodeConfig,
        }


if __name__ == "__main__":
    config = HermesConfigLoader.load_from_yaml("main.hermes")
    root_node = config.get_root_node()

    print("root_node", root_node)

    with open("schema.json", "w") as schema_file:
        schema_file.write(config.get_schema())
