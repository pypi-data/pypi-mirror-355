import logging
import threading
from typing import Callable

from .signal import Signal


class ManagedTask:
    kill_signal: bool = False
    task_active: bool = False

    stopped: Signal
    thread_handle: threading.Thread | None = None

    def __init__(self, task: Callable, name: str):
        self.task = task
        self.name = name
        self.log = logging.getLogger(f"ManagedTask[{name}]")

        self.stopped = Signal()

    def start(self):
        self.log.info(f"Starting task {self.name}")
        if self.thread_handle is not None:
            raise RuntimeError("Thread already started")

        self.kill_signal = False
        self.task_active = False

        self.thread_handle = threading.Thread(target=self.component_entrypoint, daemon=True)
        self.thread_handle.name = self.name

        self.thread_handle.start()

    def stop(self, timeout: int | None = None, block=True):
        if self.thread_handle is None:
            self.log.warning("Thread not started, cannot stop")
            return

        self.kill_signal = True

        # Check if the thread is not callin itself
        if not self.is_current_thread and block:
            self.thread_handle.join(timeout=timeout)
            self.thread_handle = None

    def component_entrypoint(self):
        # Entry point to manage the state of the component
        self.log.info(f"Task {self.name} started")
        try:
            self.task_active = True
            self.task()

        except Exception:
            self.log.exception(f"Error in {self.name} thread")

        finally:
            self.task_active = False
            self.stopped.emit()
        self.log.info(f"Task {self.name} stopped")

        # Reset the thread handle
        self.thread_handle = None

    @property
    def is_current_thread(self):
        if self.thread_handle is None:
            return False

        return threading.current_thread() == self.thread_handle
