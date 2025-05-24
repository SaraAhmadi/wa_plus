from typing import List, Dict, Any, Optional
from datetime import datetime

# Example transformation functions (these would be much more complex)


def clean_data_record(record: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Cleans a single data record."""
    cleaned_record = {}
    for key, value in record.items():
        # Basic cleaning: strip whitespace from string values
        if isinstance(value, str):
            cleaned_value = value.strip()
        else:
            cleaned_value = value

        # Handle missing value representation (e.g., convert "NA", "", "NULL" to None)
        if cleaned_value in ["NA", "", "NULL", "N/A"]:
            cleaned_record[key.strip().lower().replace(" ", "_")] = None # Standardize key
        else:
            cleaned_record[key.strip().lower().replace(" ", "_")] = cleaned_value
    return cleaned_record


def transform_data_types(record: Dict[str, Any], type_mapping: Dict[str, type]) -> Dict[str, Any]:
    """Converts fields in a record to specified Python types."""
    transformed_record = record.copy()
    for field, target_type in type_mapping.items():
        if field in transformed_record and transformed_record[field] is not None:
            try:
                if target_type == datetime and isinstance(transformed_record[field], str):
                    # Add robust date parsing, try multiple formats
                    transformed_record[field] = datetime.fromisoformat(transformed_record[field].replace('Z', '+00:00'))
                elif target_type == int:
                    transformed_record[field] = int(float(transformed_record[field])) # float first for "1.0"
                elif target_type == float:
                    transformed_record[field] = float(transformed_record[field])
                elif target_type == bool:
                    val = str(transformed_record[field]).lower()
                    transformed_record[field] = val in ["true", "1", "t", "y", "yes"]
                # Add other type conversions
            except ValueError as e:
                print(f"Warning: Could not convert field '{field}' value '{transformed_record[field]}' to {target_type}: {e}")
                transformed_record[field] = None # Or handle error differently
    return transformed_record


def calculate_derived_indicator(record: Dict[str, Any]) -> Optional[float]:
    """Example: Calculate a derived indicator if source fields exist."""
    if record.get("rainfall_mm") is not None and record.get("area_ha") is not None:
        if record["area_ha"] > 0:
            # Dummy example: rainfall depth per hectare (conceptually flawed, just for illustration)
            return record["rainfall_mm"] / record["area_ha"]
    return None


class DataTransformer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.type_mapping = self.config.get("type_mapping", {}) # e.g., {"timestamp": datetime, "value": float}

    def transform(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed_records = []
        for record in records:
            cleaned = clean_data_record(record, self.config)
            typed = transform_data_types(cleaned, self.type_mapping)
            # Example: Add a derived field
            # typed["derived_rainfall_intensity"] = calculate_derived_indicator(typed)
            transformed_records.append(typed)
        return transformed_records
