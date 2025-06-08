from abc import ABC, abstractmethod
from typing import Any, List, Dict


class BaseParser(ABC):
    """Abstract base class for data parsers."""
    def __init__(self, file_path: str, config: Optional[Dict[str, Any]] = None):
        self.file_path = file_path
        self.config = config or {}

    @abstractmethod
    def parse(self) -> List[Dict[str, Any]]:
        """Parses the data file and returns a list of records (dictionaries)."""
        pass

    def validate_file(self) -> bool:
        """Basic file validation (e.g., existence, readability)."""
        import os
        if not os.path.exists(self.file_path) or not os.path.isfile(self.file_path):
            print(f"Error: File not found or is not a file: {self.file_path}")
            return False
        # Add more validation if needed (e.g., file size, extension)
        return True
