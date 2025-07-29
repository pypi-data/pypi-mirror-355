from abc import ABC, abstractmethod


class CheckResult:
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


class BaseCheck(ABC):
    name: str = None
    description: str = ""

    def __init__(self):
        self.status = None  
        self.message = ""

    @abstractmethod
    def run(self):
        pass