import time
from typing import List

import click
from node_hermes_core.nodes.depedency import HermesDependencies
from node_hermes_core.loader import load_modules
from .config_loader import HermesConfigLoader
import json


@click.group()
def cli():
    pass


@cli.command()
@click.option("--output", "-o", required=True, help="Output schema file")
@click.option("--packages", "-p", multiple=True, help="Packages to load", default=None)
@click.option("--config", "-c", help="Config file", default=None)
def schema(output: str, packages: List[str] | None, config: str | None):
    if config:
        modules = HermesDependencies.import_from_yaml(config)
    elif packages:
        modules = load_modules(packages)
    else:
        raise ValueError("Either --config or --packages must be specified")

    print("Loaded modules:")
    for module in modules:
        print(f" - {module.__name__}")

    # Create the ConfigModel
    models = HermesConfigLoader.get_config_model(modules)

    with open(output, "w") as schema_file:
        schema_file.write(json.dumps(models["LocalHermesConfig"].model_json_schema()))
    
    print(f"Schema written to {output}")
    

@cli.command()
@click.argument("config_path", type=str)
def run(config_path: str):
    config = HermesConfigLoader.load_from_yaml(config_path)
    root_node = config.get_root_node()
    root_node.attempt_init()

    while True:
        time.sleep(1)


def generate_schema():
    cli()


if __name__ == "__main__":
    cli()
