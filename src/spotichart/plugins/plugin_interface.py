from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str

class IPlugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        pass

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass
