import csv
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser


class CSVParser(BaseParser):
    def __init__(self, file_path: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(file_path, config)
        self.delimiter = self.config.get("delimiter", ",")
        self.quotechar = self.config.get("quotechar", '"')
        self.expected_headers = self.config.get("expected_headers", None) # Optional list

    def parse(self) -> List[Dict[str, Any]]:
        if not self.validate_file():
            return []

        records: List[Dict[str, Any]] = []
        try:
            with open(self.file_path, mode='r', encoding=self.config.get('encoding', 'utf-8-sig')) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=self.delimiter, quotechar=self.quotechar)
                if self.expected_headers and set(self.expected_headers) != set(reader.fieldnames or []):
                    print(f"Warning: CSV headers mismatch for {self.file_path}.")
                    print(f"Expected: {self.expected_headers}, Got: {reader.fieldnames}")
                    # Decide on error handling: skip file, try to map, etc.

                for row in reader:
                    records.append(dict(row)) # Convert OrderedDict to dict
        except Exception as e:
            print(f"Error parsing CSV file {self.file_path}: {e}")
            # Handle error appropriately
        return records
