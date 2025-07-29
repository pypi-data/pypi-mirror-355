from abc import ABC, abstractmethod
from typing import List, Any, Dict


class Chart(ABC):

    def __init__(self, dataset: List[List[Any]], dimensions: List[str], config: Dict = None):
        if config is None:
            config = {}

        self.config = config
        self.dataset = dataset
        self.dimensions = dimensions

    @abstractmethod
    def get_options(self):
        pass
