from abc import ABC, abstractmethod

class ISingleton(ABC):
    @staticmethod
    @abstractmethod
    def get_instance():
        """Implement in child class"""