import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from frictionless import Check, Schema, errors, validate


def get_resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# --- Custom Errors ---
class DecimalPrecisionError(errors.CellError):
    code = "decimal-precision-error"
    name = "Decimal Precision Error"
    tags = ["#body"]
    template = "Value {value} does not match Decimal({precision}, {scale}). {note}"
    description = "Value exceeds defined decimal precision or scale."


class NullIslandError(errors.RowError):
    code = "null-island-error"
    name = "Null Island Coordinates"
    tags = ["#body"]
    template = "Coordinates are exactly (0,0)."
    description = "Lat/Lon cannot be (0,0)."


# --- Custom Checks ---
class DecimalPrecisionCheck(Check):
    Errors = [DecimalPrecisionError]

    def validate_row(self, row):
        for field in self.resource.schema.fields:
            if field.type != "number" or not field.constraints:
                continue

            max_prec = field.constraints.get("decimalPrecision")
            max_scale = field.constraints.get("decimalScale")

            if max_prec is None:
                max_prec = field.custom.get("decimalPrecision")
            if max_scale is None:
                max_scale = field.custom.get("decimalScale")

            if not max_prec or not max_scale:
                continue

            val = row[field.name]
            if val is None:
                continue

            try:
                d = Decimal(str(val))
                dt = d.as_tuple()
                scale = abs(dt.exponent) if dt.exponent < 0 else 0
                num_digits = len(dt.digits)
                int_part = max(0, num_digits - scale)

                if scale > max_scale:
                    yield DecimalPrecisionError.from_row(
                        row,
                        note=f"Scale {scale} > {max_scale}",
                        field_name=field.name,
                        value=val,
                        precision=max_prec,
                        scale=max_scale,
                    )
                elif (int_part + scale) > max_prec:
                    yield DecimalPrecisionError.from_row(
                        row,
                        note=f"Precision {int_part + scale} > {max_prec}",
                        field_name=field.name,
                        value=val,
                        precision=max_prec,
                        scale=max_scale,
                    )
            except (ValueError, InvalidOperation):
                pass


class GeoLogicCheck(Check):
    Errors = [NullIslandError]

    def validate_row(self, row):
        lat = row.get("lat")
        lon = row.get("lon")
        if lat is None or lon is None:
            return

        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (ValueError, TypeError):
            return

        # 1. Error on Null Island (0,0)
        if lat_f == 0.0 and lon_f == 0.0:
            yield NullIslandError.from_row(row, note="")
            return

        # 2. Warning on Bounds (Continental US: 24N to 50N, 125W to 66W)
        MIN_LAT, MAX_LAT = 24.0, 50.0
        MIN_LON, MAX_LON = -125.0, -66.0

        in_bounds = (MIN_LAT <= lat_f <= MAX_LAT) and (MIN_LON <= lon_f <= MAX_LON)

        if not in_bounds:
            # Check if swapped
            swapped_ok = (MIN_LAT <= lon_f <= MAX_LAT) and (MIN_LON <= lat_f <= MAX_LON)

            print(
                f"\n⚠️  WARNING (Row {row.row_number}): Location {lat_f}, {lon_f} outside US bounds."
            )
            if swapped_ok:
                print(f"    POSSIBLE SWAP DETECTED. Did you mean: {lon_f}, {lat_f}?")
            print(
                f"    Verify: https://www.google.com/maps/search/?api=1&query={lat_f},{lon_f}"
            )


# --- Main ---
def main():
    import json

    print("-" * 60)
    print("   AQDx Local Validator Tool (v1.0)")
    print("-" * 60)

    if len(sys.argv) < 2:
        print("\nUsage: Drag and drop your CSV/XLSX file onto this executable.")
        print("       OR run from command line: validate_aqdx.exe <filename>")
        input("\nPress Enter to exit...")
        sys.exit(1)

    raw_path = sys.argv[1]
    path_obj = Path(raw_path).resolve()

    # --- FIX: Use Relative Path to bypass "Path is not safe" error ---
    # Frictionless rejects absolute paths on Windows (e.g. C:\Users\...) as "unsafe".
    # We must convert it to a relative path from the current working directory.
    try:
        # Get path relative to where the script/exe is running
        data_file_path = os.path.relpath(path_obj, os.getcwd())
    except ValueError:
        # Fallback: If file is on a different drive, we must use absolute path.
        # This is rare for drag-and-drop usage.
        data_file_path = str(path_obj)

    print(f"DEBUG: Validating File (Relative): {data_file_path}")

    schema_file = get_resource_path("aqdx-schema-tabular.json")

    # Check existence using the absolute path object (safe)
    if not path_obj.exists():
        print(f"\nError: File not found: {str(path_obj)}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    if not os.path.exists(schema_file):
        print(f"\nCRITICAL: Bundled schema not found at {schema_file}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print(f"\nValidating: {os.path.basename(data_file_path)}")
    print("Processing...")

    try:
        # 1. Load schema contents (bypasses schema path safety checks)
        with open(schema_file, "r", encoding="utf-8") as f:
            schema_descriptor = json.load(f)

        schema = Schema.from_descriptor(schema_descriptor)

        # 2. Pass the RELATIVE path string to validate()
        #    This avoids the 'trusted' keyword error and the 'not safe' path error.
        report = validate(
            data_file_path,
            schema=schema,
            checks=[DecimalPrecisionCheck(), GeoLogicCheck()],
        )

        print("-" * 60)
        if report.valid:
            print("✔ SUCCESS: File is valid AQDx format!")
        else:
            print(f"✘ FAILURE: {report.stats['errors']} error(s) found.")
            print("-" * 60)

            if report.errors:
                print("CRITICAL FILE ERRORS:")
                for err in report.errors:
                    print(f" - Error Code: {err.code}")
                    print(f" - Message:    {err.message}")
                    if err.note:
                        print(f" - Note:       {err.note}")
                print("-" * 90)

            elif report.tasks:
                print(f"{'Row':<5} | {'Field':<15} | {'Error Code':<25} | {'Message'}")
                print("-" * 120)

                count = 0
                error_list = report.tasks[0].flatten(
                    ["rowNumber", "fieldNumber", "fieldName", "code", "message"]
                )

                for err in error_list:
                    count += 1
                    row = str(err[0]) if err[0] is not None else "-"
                    field = str(err[2]) if err[2] else str(err[1]) if err[1] else "-"
                    code = str(err[3])
                    msg = str(err[4])

                    print(f"{row:<5} | {field:<15} | {code:<25} | {msg}")

                    if count >= 50:
                        print("\n... (Display stopped after 50 errors)")
                        break

    except Exception as e:
        print(f"\nCRITICAL UNHANDLED ERROR: {e}")
        import traceback

        traceback.print_exc()

    print("-" * 60)
    input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
