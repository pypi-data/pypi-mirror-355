import time


class Timer:
    def __init__(self):
        self.filter_factor = 0.9
        self.average_runtime = 0

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()
        self.runtime = self.end_time - self.start_time
        self.average_runtime = self.filter_factor * self.average_runtime + (1 - self.filter_factor) * self.runtime
        return self.runtime


class FrequencyCounter:
    def __init__(self):
        self.last_update_time = time.time()
        self.delta_counts = 0
        self.total_counts = 0
        self.last_frequency = 0
        self.last_packet_timestamp = time.time()

    def update(self, count, timestamp: float | None = None):
        self.delta_counts += count
        self.total_counts += count

        if timestamp is not None:
            self.last_packet_timestamp = timestamp
        else:
            self.last_packet_timestamp = time.time()

        self.update_frequency()

    def update_frequency(self):
        if time.time() - self.last_update_time > 1:
            self.last_frequency = self.delta_counts / (time.time() - self.last_update_time)
            self.delta_counts = 0
            self.last_update_time = time.time()

    @property
    def frequency(self):
        return self.last_frequency

    @property
    def count(self):
        return self.total_counts

    @property
    def last_packet_age(self):
        return time.time() - self.last_packet_timestamp
