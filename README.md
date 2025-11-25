# AQDx Local Validator

A simple, standalone tool for validating air quality data against the **AQDx Standard (July 2024)**. 

This tool allows local air agencies and community groups to verify their data files (CSV, XLSX, Parquet) locally before submission to CDPHE, ensuring all fields meet the strict type, pattern, and precision requirements of the AQDx schema.

## Quick Usage Guide

### Windows Users
**No installation required.**

1.  **Download** the latest `aqdx-validator-windows.zip` from the [Releases Page](../../releases).
2.  **Unzip** the file. You will see `aqdx-validator-windows.exe`.
3.  **Drag and Drop** your data file (`.csv` or `.xlsx`) directly onto the `.exe` icon.
4.  A window will open showing the validation results.
    *   **Green Message:** Success! Your file is ready to submit.
    *   **Red Table:** Errors found. Fix the issues listed and try again.

### For Mac/Linux Users
1.  Download the binary for your OS from the [Releases Page](../../releases).
2.  Open a terminal.
3.  Run the tool against your file:
    ```
    ./aqdx-validator-macos my_data.csv
    ```
    *(Note: You may need to run `chmod +x aqdx-validator-macos` first to make it executable.)*

---

## Checks Performed

This tool enforces the **AQDx Tabular Schema** using strict validation rules:

1.  **Data Structure:**
    *   Verifies all required columns are present.
    *   Checks for correct data types (e.g., `datetime` must be ISO 8601, `value` must be numeric).

2.  **Decimal Precision (Custom Check):**
    *   Enforces SQL-style `Decimal(9,5)` limits on measurement values and coordinates.
    *   **Max Scale:** 5 digits after the decimal point (e.g., `10.12345` is ok, `10.123456` fails).
    *   **Max Precision:** 9 total digits (e.g., `1234.12345` is ok, `12345.12345` fails).

3.  **Pattern & Logic:**
    *   **Device IDs:** Must not contain commas or periods.
    *   **Codes:** Verifies AQS codes (e.g., `parameter_code` must be exactly 5 digits).
    *   **Null Island:** Explicitly fails if coordinates are exactly `(0,0)`.

4.  **Geographic Warnings (Non-Breaking):**
    *   Checks if coordinates fall within the Continental US.
    *   **Smart Warning:** If points are out of bounds, it checks if Lat/Lon might be swapped and prints a warning with a Google Maps verification link.

---
