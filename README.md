# AQDx Validation Toolkit

This repository provides the tools and documentation necessary to validate data air quality data against the AQDx (Air Quality Data eXchange) specification.

## Quick Start: Command-Line Validation

This is the fastest and simplest way to check your data file.

### Step 1: Setup Your Environment and install the frictionless package (One-Time Setup)

Before you can run the validator, you need to set up a clean environment and install the necessary software. This is a one-time process.

**1. Create a Virtual Environment**

It is highly recommended to use a virtual environment to avoid conflicts with other Python projects. Open your terminal or command prompt and choose one of the options below.

*   **Option A: Using `venv` (standard with Python)**
    ```
    # Navigate to your desired folder and create the environment
    python -m venv aqdx-env

    # Activate it (you must do this each time you open a new terminal)
    # On macOS/Linux:
    source aqdx-env/bin/activate
    # On Windows:
    aqdx-env\Scripts\activate

    pip install frictionless
    ```

*   **Option B: Using `conda` (must first install miniforge)**
    ```
    # Create and activate the environment
    conda create -n aqdx-env frictionless -y
    conda activate aqdx-env
    ```

*   **Option C: Install to System Python**
    *   If you do not need virtual environments (i.e. you do not use python for any other projects), you can install the required packages directly to your system's main Python 
    *   No activation step is needed for this option.
    ```
    pip install frictionless
    ```


### Step 2: Run the Validator

After the one-time setup, validating a file is a single command. Make sure the schema file (`aqdx-schema-tabular.json`) from this repository is in the same directory as your data file.

1.  **To validate a file (e.g., `my_aqdx_data.csv` or `my_aqdx_data.xlsx`):**
 
    ```
    frictionless validate my_aqdx_data.csv --schema aqdx-schema-tabular.json
    ```

2.  **Interpreting the Results:**
    *   If your file is **valid**, the command will finish silently with no output.
    *   If your file is **invalid**, you will see a detailed error report in your terminal, showing exactly which rows and cells have problems.

    **Example Error Output:**
    ```
    +------+-----+------------------+---------------------------------------------+
    | row  | col | field            | message                                     |
    +======+=====+==================+=============================================+
    |    3 |   6 | parameter_code   | The cell has a length of 36 which is        |
    |      |     |                  | greater than the maximum length of 16       |
    +------+-----+------------------+---------------------------------------------+
    |    4 |   7 | value            | The value "'not a number'" is not a valid    |
    |      |     |                  | number                                      |
    +------+-----+------------------+---------------------------------------------+
    ```

## Detailed Analysis with Jupyter Notebook

For a more interactive way to explore validation errors and work with the data, see the `validate_a_local_file.ipynb` notebook included in this repository. It is intended for users who are comfortable with Python and want to programmatically inspect the validation report.
