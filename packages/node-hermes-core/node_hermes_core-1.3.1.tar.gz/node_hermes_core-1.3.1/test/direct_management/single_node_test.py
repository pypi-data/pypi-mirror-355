import time

from node_hermes_core.built_in.test_nodes import NoiseNode
from node_hermes_core.utils.log_setup import setup_logging

setup_logging()


config = NoiseNode.Config(type="noise")
config.name = "NoiseNode"
noise_node = NoiseNode(config)
noise_node.init()

while True:
    print(noise_node.get_data().as_flat_dict())
    time.sleep(1)
