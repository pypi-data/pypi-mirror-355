from pydantic import Field

from ..data.datatypes import GenericDataPacket
from ..links.queued_link import QueuedLink
from .generic_node import GenericNode


class SinkNode(GenericNode):
    class Config(GenericNode.Config):
        source: QueuedLink.Config = Field(default_factory=QueuedLink.Config.default)

    base_sink: QueuedLink

    def __init__(self, config: Config | None):
        GenericNode.__init__(self, config=config)
        assert config is not None, "Config is None"
        self.base_sink = QueuedLink(config=config.source)
        self.sink_port_manager.add("input", self.base_sink)

    def init(self):
        super().init()
        self.base_sink.reset()

    def put_data(self, data: GenericDataPacket | None):
        self.base_sink.put_data(data)

    def get_data(self) -> GenericDataPacket | None:
        return self.base_sink.get_data()

    def has_data(self) -> bool:
        return self.base_sink.has_data()

    @property
    def info_string(self) -> str:
        return f"{self.base_sink.frequency_counter.frequency:.2f} Hz"

    @property
    def queue_string(self) -> str:
        return f"{self.base_sink.queue.qsize()} items in queue"
