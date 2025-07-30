from queue import Empty, Queue
from typing import Literal

from node_hermes_core.data.datatypes import GenericDataPacket
from node_hermes_core.utils.frequency_counter import FrequencyCounter
from pydantic import BaseModel, ConfigDict, Field

from .generic_link import GenericLink


class QueuedLink(GenericLink):
    """A data target that uses a queue to store data"""

    class Config(BaseModel):
        # Dont allow any other type than "queued_link"
        model_config = ConfigDict(extra="forbid")  # Don't allow extra fields

        type: Literal["queued_link"]
        queue_size: int = 1000
        nodes: list[str] = Field(default_factory=list)

        @classmethod
        def default(cls) -> "QueuedLink.Config":
            return cls(type="queued_link")

    queue: Queue

    def __init__(self, config: Config):
        self.config = config
        self.queue = Queue(maxsize=self.config.queue_size)
        self.frequency_counter = FrequencyCounter()

    def put_data(self, data):
        if self.queue.full():
            return

        self.queue.put(data)
        self.frequency_counter.update(len(data))

    def get_data(self, timeout=1) -> GenericDataPacket | None:
        try:
            return self.queue.get(timeout=timeout)
        except Empty:
            return None

    def has_data(self):
        return not self.queue.empty()

    def reset(self):
        # Remove all elements from the queue
        while not self.queue.empty():
            self.queue.get()
