from node_hermes_core.loader import import_nodes

import_nodes("hermes_core.built_in.test_nodes")
import_nodes("hermes_core.built_in.output")
import_nodes("hermes_core.built_in.operation_nodes")
import_nodes("virenti_nodes")

import logging
import time

# from node_hermes_core.built_in.output import CSVWriterNode
from node_hermes_core.built_in.test_nodes import NoiseNode, SineNode
from node_hermes_core.links import QueuedLink
from node_hermes_core.nodes.root_nodes import GroupNode, RootNode, WorkerNode

logging.basicConfig(level=logging.DEBUG)

node = RootNode(
    RootNode.Config(
        type="root",
        nodes={
            "logger_worker": WorkerNode.Config(
                type="worker",
                nodes={
                    "group": GroupNode.Config(
                        type="group",
                        nodes={
                            "noise": NoiseNode.Config(type="noise"),
                            "sine": SineNode.Config(type="sine"),
                        },
                    ),
                },
            ),
            "output_worker": WorkerNode.Config(
                type="worker",
                nodes={
                    # "csv_writer": CSVWriterNode.Config(
                    #     type="csv_writer",
                    #     filename="output.csv",
                    #     source=QueuedLink.Config(
                    #         type="queued_link",
                    #         nodes=[
                    #             "logger_worker.group.*",
                    #         ],
                    #     ),
                    # ),
                },
            ),
        },
    ),
)

node.attempt_init()

time.sleep(10)
