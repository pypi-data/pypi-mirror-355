import time

from node_hermes_core.config_loader import HermesConfigLoader
from node_hermes_core.nodes.depedency import HermesDependencies

# config_path = r"packages\datacapture-core\test\yaml\basic_config.hermes"
config_path = r"packages\datacapture-core\test\yaml\single_line_printer.hermes"

# # Load the required modules in order to be able to parse the full configuration
# HermesDependencies.import_from_yaml(config_path)

# # Reload the configuration
# import logging

# from node_hermes_core.nodes.root_nodes import HermesConfig

# logging.basicConfig(level=logging.DEBUG)


# output = "schema.json"
# with open(output, "w") as schema_file:
#     schema_file.write(HermesConfig.get_schema_json())


# config = HermesConfig.from_yaml(config_path)
# root_node = config.get_root_node()
# root_node.attempt_init()

config = HermesConfigLoader.load_from_yaml(config_path)
root_node = config.get_root_node()
root_node.attempt_init()
    
while True:
    time.sleep(1)
