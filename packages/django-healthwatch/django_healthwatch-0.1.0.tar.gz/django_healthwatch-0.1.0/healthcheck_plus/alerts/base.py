from abc import ABC, abstractmethod

class BaseAlerter(ABC):
    @abstractmethod
    def send(self, check_name, status, message):
        pass
