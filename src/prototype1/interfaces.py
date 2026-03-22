from abc import ABC, abstractmethod
from typing import Dict, Any


class ExtractionEngine(ABC):
    @abstractmethod
    def extract_rows(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        Standard extraction interface.

        Expected return keys:
        - records
        - summary
        - run_path
        """
        pass