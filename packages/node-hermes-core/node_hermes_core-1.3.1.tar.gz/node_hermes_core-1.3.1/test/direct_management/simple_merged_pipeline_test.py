import time

from node_hermes_core.built_in.operation_nodes import AggegatorNode
from node_hermes_core.built_in.test_nodes import SineNode
from node_hermes_core.utils.log_setup import setup_logging

setup_logging()

merge = AggegatorNode(
    AggegatorNode.Config(
        type="aggregator",
        buffering_delay=1,
        interpolation=AggegatorNode.InterpolationConfig(mode="linear"),
        resampling=AggegatorNode.ResamplingConfig(interval="100ms"),
    )
)
merge.init()
sins: list[SineNode] = []

for i in range(10):
    sin = SineNode(SineNode.Config(type="sine", amplitude=1, frequency=1, offset=0))
    sin.base_target.add_target(merge.base_sink)
    sin.init()
    sins.append(sin)

while True:
    time.sleep(1)
    for sin in sins:
        sin.work()

    data = merge.work()
    if data is not None:
        print(data.as_flat_dict())
