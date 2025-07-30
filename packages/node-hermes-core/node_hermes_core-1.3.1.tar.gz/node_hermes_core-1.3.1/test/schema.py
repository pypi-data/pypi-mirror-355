import json

from node_hermes_core.config_loader import HermesConfigLoader
from node_hermes_core.nodes.depedency import HermesDependencies

PATH = r"packages\datacapture-core\test\yaml\basic_config.hermes"

modules = HermesDependencies.import_from_yaml(PATH)

print("Loaded modules:")
for module in modules:
    print(f" - {module.__name__}")

models = HermesConfigLoader.get_config_model(modules)


output = "schema.json"
with open(output, "w") as schema_file:
    schema_file.write(json.dumps(models["LocalHermesConfig"].model_json_schema()))
