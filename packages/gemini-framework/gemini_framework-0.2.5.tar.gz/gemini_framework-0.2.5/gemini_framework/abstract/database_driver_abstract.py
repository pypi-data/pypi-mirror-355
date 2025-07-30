from abc import ABC, abstractmethod


class DatabaseDriverAbstract(ABC):
    """Abstract class for Database Driver."""

    def __init__(self):
        self.conn = None
        self.parameters = dict()

    def update_parameters(self, parameters):
        for key, value in parameters.items():
            self.parameters[key] = value

    def disconnect(self):
        self.conn = None

    @abstractmethod
    def connect(self):
        return

    @abstractmethod
    def read_data(self):
        return

    @abstractmethod
    def write_data(self):
        return
