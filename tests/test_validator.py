import json
import os

import pytest
from frictionless import Detector, Resource, Schema, validate

from src.validate_aqdx import DecimalPrecisionCheck, GeoLogicCheck

# Config
TEST_FILES_DIR = "test_files"
SCHEMA_PATH = "src/aqdx-schema-tabular.json"

# Test Matrix
TEST_CASES = [
    ("valid_example.csv", True, []),
    ("error_precision.csv", False, ["decimal-precision-error"]),
    ("error_null_island.csv", False, ["null-island-error"]),
    ("warn_lat_lon_swap.csv", True, []),
    ("error_pattern.csv", False, ["constraint-error"]),
    ("error_required.csv", False, ["missing-label"]),
    ("valid_column_swap.csv", True, []),
]


@pytest.mark.parametrize("filename, expected_valid, expected_errors", TEST_CASES)
def test_file_validation(filename, expected_valid, expected_errors):
    """Runs validation against real files and checks for specific error codes."""
    filepath = os.path.join(TEST_FILES_DIR, filename)
    if not os.path.exists(filepath):
        pytest.fail(f"Test file missing: {filepath}")

    # === FIX 1: Apply same schema filtering logic as main script ===
    # Read actual headers from the file
    actual_headers = []
    try:
        with Resource(filepath) as resource:
            actual_headers = resource.header
    except Exception:
        pass  # Will be caught by validation

    # Load and filter schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_descriptor = json.load(f)

    final_fields = []
    for field in schema_descriptor.get("fields", []):
        name = field.get("name")
        constraints = field.get("constraints", {})
        is_required = constraints.get("required", False)

        # Keep field if it exists in file OR if it is mandatory
        if name in actual_headers:
            final_fields.append(field)
        elif is_required:
            final_fields.append(field)  # Kept to trigger missing-label error

    # Update descriptor with filtered fields
    schema_descriptor["fields"] = final_fields
    schema = Schema.from_descriptor(schema_descriptor)

    # === FIX 2: Add Detector with schema_sync=True ===
    report = validate(
        filepath,
        schema=schema,
        detector=Detector(schema_sync=True),
        checks=[DecimalPrecisionCheck(), GeoLogicCheck()],
    )

    # 1. Check Validity Status
    assert report.valid == expected_valid, (
        f"File {filename}: Expected valid={expected_valid}, got {report.valid}. "
        f"Errors: {report.flatten(['code', 'message'])}"
    )

    # 2. Check Specific Error Codes if failure expected
    if not expected_valid and expected_errors:
        # === FIX 3: Correct error code extraction ===
        found_codes = set()
        for task in report.tasks:
            # Access errors directly and get their code attribute
            for error in task.errors:
                # Try to get 'code' attribute first, fall back to 'type'
                error_code = getattr(error, "code", None) or getattr(
                    error, "type", None
                )
                if error_code:
                    found_codes.add(error_code)

        for code in expected_errors:
            assert code in found_codes, (
                f"File {filename}: Expected error '{code}' not found. Found: {found_codes}"
            )
