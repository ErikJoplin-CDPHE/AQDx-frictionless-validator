import sys
import os
import json
from decimal import Decimal, InvalidOperation
from frictionless import validate, Schema, Check, errors, system

# --- 1. Custom Check Implementation ---
class DecimalPrecisionError(errors.CellError):
    """
    Custom error to report when a number fails precision/scale checks.
    """
    code = "decimal-precision-error"
    name = "Decimal Precision Error"
    tags = ["#body"]
    template = "Value {value} does not match Decimal({precision}, {scale}). {note}"
    description = "The value must match the specified decimal precision and scale."

class DecimalPrecisionCheck(Check):
    """
    Reads 'decimalPrecision' and 'decimalScale' from field constraints
    and validates numeric values against them.
    """
    Errors = [DecimalPrecisionError]

    def validate_row(self, row):
        for field in self.resource.schema.fields:
            # optimization: skip if not a number or no constraints exist
            if field.type != "number" or not field.constraints:
                continue

            # Retrieve the custom constraints from the schema
            max_precision = field.constraints.get("decimalPrecision")
            max_scale = field.constraints.get("decimalScale")

            # If the schema doesn't have these keys, skip this field
            if not max_precision or not max_scale:
                continue

            value = row[field.name]

            # Skip nulls (standard 'required' check handles missing values)
            if value is None:
                continue

            try:
                # Convert to Decimal for accurate digit counting
                # We use str(value) because float conversion can introduce artifacts
                d = Decimal(str(value))
                
                # Get tuple of digits (sign, digits, exponent)
                dt = d.as_tuple()
                
                # Exponent is negative for decimals (e.g., 0.12 -> exp -2)
                exponent = dt.exponent
                scale = abs(exponent) if exponent < 0 else 0
                
                # Number of significant digits
                num_digits = len(dt.digits)
                
                # Calculate integer part length
                # For 0.123, digits=(1,2,3) len=3, scale=3 -> int_part=0
                # For 10.5, digits=(1,0,5) len=3, scale=1 -> int_part=2
                int_part_len = num_digits - scale
                if int_part_len < 0: 
                    int_part_len = 0
                
                # Precision = integer digits + scale (SQL definition)
                actual_precision = int_part_len + scale

                # --- The Checks ---
                
                # 1. Check Scale (digits to the right)
                if scale > max_scale:
                    yield DecimalPrecisionError.from_row(
                        row, 
                        note=f"Scale is {scale}, max allowed is {max_scale}.", 
                        field_name=field.name, 
                        value=value, 
                        precision=max_precision, 
                        scale=max_scale
                    )

                # 2. Check Precision (total digits)
                elif actual_precision > max_precision:
                    yield DecimalPrecisionError.from_row(
                        row, 
                        note=f"Total precision is {actual_precision}, max allowed is {max_precision}.", 
                        field_name=field.name, 
                        value=value, 
                        precision=max_precision, 
                        scale=max_scale
                    )

            except (ValueError, InvalidOperation):
                # If it's not a valid number, standard frictionless type checking 
                # will catch it, so we pass silently here.
                pass

# --- 2. Main Execution Logic ---
def main():
    print("------------------------------------------------------------")
    print("   AQDx Local Validator Tool (v1.0)")
    print("------------------------------------------------------------")

    # Check for arguments
    if len(sys.argv) < 2:
        print("\nUsage: Drag and drop your CSV file onto this executable.")
        print("       OR run from command line: validate_aqdx.exe <filename>")
        input("\nPress Enter to exit...")
        sys.exit(1)

    data_file = sys.argv[1]
    
    # Determine schema path (looks in the same folder as the exe/script)
    if getattr(sys, 'frozen', False):
        # If running as compiled exe
        application_path = os.path.dirname(sys.executable)
    else:
        # If running as python script
        application_path = os.path.dirname(os.path.abspath(__file__))
        
    schema_file = os.path.join(application_path, "aqdx-schema-tabular.json")

    # Check if files exist
    if not os.path.exists(data_file):
        print(f"\nError: Data file not found: {data_file}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    if not os.path.exists(schema_file):
        print(f"\nError: Schema file not found: {schema_file}")
        print("Make sure 'aqdx-schema-tabular.json' is in the same folder as this tool.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print(f"\nValidating file: {os.path.basename(data_file)}")
    print(f"Using schema:    {os.path.basename(schema_file)}")
    print("\nProcessing... please wait.")

    try:
        # Load schema
        schema = Schema.from_descriptor(schema_file)
        
        # Run validation with our custom check
        report = validate(
            data_file,
            schema=schema,
            checks=[DecimalPrecisionCheck()]
        )

        print("------------------------------------------------------------")
        if report.valid:
            print("✔ SUCCESS: The file is valid AQDx format!")
        else:
            print(f"✘ FAILURE: Found {report.stats['errors']} error(s).")
            print("------------------------------------------------------------")
            
            # Print readable error table
            # We flatten the report to get a simple list of errors
            error_list = report.flatten(["rowNumber", "fieldNumber", "fieldName", "code", "message"])
            
            # simple format for console output
            print(f"{'Row':<5} | {'Field':<15} | {'Error Code':<25} | {'Message'}")
            print("-" * 90)
            
            count = 0
            for err in error_list:
                count += 1
                # Extract values (handling potential None values)
                row = str(err[0]) if err[0] else "-"
                field = str(err[2]) if err[2] else "-"
                code = str(err[3])
                msg = str(err[4])
                
                # Truncate long messages
                if len(msg) > 60: msg = msg[:57] + "..."
                
                print(f"{row:<5} | {field:<15} | {code:<25} | {msg}")
                
                if count >= 50:
                    print("\n... (Stopping display after 50 errors)")
                    break

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("------------------------------------------------------------")
    # Keep window open for user to read results
    input("\nPress Enter to close...")

if __name__ == "__main__":
    main()
