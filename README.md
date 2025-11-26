# AQDx Local Validator

A simple, standalone tool for validating air quality data against the [AQDx Standard (July 2024)](https://cdphe.colorado.gov/air-quality-data-exchange).

This tool allows local air agencies and community groups to verify their data files (CSV, XLSX, Parquet) locally before submission to CDPHE, ensuring all fields meet the strict type, pattern, and precision requirements of the AQDx schema.

## Quick Usage Guide

### Windows Users
**No installation required.**

1.  **Download** the latest `aqdx-validator-windows.exe` file from the [Releases Page](../../releases).
2.  **Drag and Drop** your data file (`.csv`) directly onto the `.exe` icon.
3.  A window will open showing the validation results.
    *   **Green Message:** Success! Your file is ready to submit.
    *   **Red Table:** Errors found. Fix the issues listed and try again.

### For Mac/Linux Users (Run from Source)
We do not currently provide pre-built binaries for macOS or Linux. You can run the validator directly from the source code.

1.  **Clone or Download** this repository.
2.  Ensure you have **Python 3.12+** installed.
3.  Install the required dependencies:
    ```
    pip install frictionless openpyxl pyarrow
    ```
4.  Run the validator script against your data file:
    ```
    python src/validate_aqdx.py /path/to/your_data.csv
    ```

---

## Checks Performed

This tool enforces the **AQDx Tabular Schema** using strict validation rules:

1.  **Data Structure:**
    *   Verifies all required columns are present.
    *   Checks for correct data types (e.g., `datetime` must be ISO 8601, `value` must be numeric).

2.  **Decimal Precision and Scale:**
    *   Enforces SQL-style e.g. `Decimal(p, s)` limits on measurement values and coordinates.
    *   e.g. Decimal(9, 5)
        *   **Max Scale:** 5 digits after the decimal point (e.g., `10.12345` is ok, `10.123456` fails).
        *   **Max Precision:** 9 total digits (e.g., `1234.12345` is ok, `12345.12345` fails).

3.  **Pattern & Logic:**
    *   **Device IDs:** Must not contain commas or periods.
    *   **Codes:** Verifies AQS codes (e.g., `parameter_code` must be exactly 5 digits).
    *   **Null Island:** Explicitly fails if coordinates are exactly `(0,0)`.

4.  **latitude and longitude check:**
    *   Checks if coordinates fall within the Continental US.
    *   **Smart Warning:** If points are out of bounds, it checks if Lat/Lon might be swapped and prints a warning with a Google Maps verification link.

---