import os
import pytest
from frictionless import validate, Schema
from src.validate_aqdx import DecimalPrecisionCheck, GeoLogicCheck

# Config
TEST_FILES_DIR = "test_files"
SCHEMA_PATH = "src/aqdx-schema.json"

# Test Matrix: (filename, expected_valid, [expected_error_codes])
TEST_CASES = [
    # 1. Valid Data
    ("valid_example.csv", True, []),

    # 2. Decimal Precision (Custom Check)
    ("error_precision.csv", False, ["decimal-precision-error"]),

    # 3. Null Island (Custom Check)
    ("error_null_island.csv", False, ["null-island-error"]),

    # 4. Schema Pattern (Standard Check, e.g. bad Device ID characters)
    ("error_pattern.csv", False, ["pattern-constraint"]),

    # 5. Missing Required Fields (Standard Check)
    ("error_required.csv", False, ["required-constraint"]),
]

@pytest.mark.parametrize("filename, expected_valid, expected_errors", TEST_CASES)
def test_file_validation(filename, expected_valid, expected_errors):
    """Runs validation against real files and checks for specific error codes."""
    
    file_path = os.path.join(TEST_FILES_DIR, filename)
    if not os.path.exists(file_path):
        pytest.fail(f"Test file missing: {file_path}")

    schema = Schema.from_descriptor(SCHEMA_PATH)
    
    # Must verify using the exact same custom checks as main script
    report = validate(
        file_path,
        schema=schema,
        checks=[DecimalPrecisionCheck(), GeoLogicCheck()]
    )

    # 1. Check Validity Status
    assert report.valid == expected_valid, \
        f"File {filename}: Expected valid={expected_valid}, got {report.valid}. Errors: {report.flatten(['code', 'message'])}"

    # 2. Check Specific Error Codes (if failure expected)
    if not expected_valid and expected_errors:
        found_codes = [err[0] for err in report.flatten(["code"])]
        for code in expected_errors:
            assert code in found_codes, \
                f"File {filename}: Expected error '{code}' not found. Found: {found_codes}"
