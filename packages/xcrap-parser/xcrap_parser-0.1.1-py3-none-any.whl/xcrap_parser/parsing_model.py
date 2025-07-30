from abc import ABC, abstractmethod

class ParsingModel(ABC):
    @abstractmethod
    def parse(self, source: str) -> ...:
        ...