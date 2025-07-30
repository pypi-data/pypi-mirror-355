class Signal:
    def __init__(self):
        self.targets = []

    def connect(self, callback):
        self.targets.append(callback)

    def disconnect(self, callback):
        self.targets.remove(callback)

    def emit(self):
        for target in self.targets:
            target()
