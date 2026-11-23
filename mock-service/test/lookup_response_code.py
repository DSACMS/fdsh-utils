#!/usr/bin/env python3

import csv
import sys
from pathlib import Path

CSV_FILE = Path(__file__).with_name("mesh_response_codes.csv")


def usage() -> None:
    print(f"Usage: {Path(sys.argv[0]).name} RESPONSE_CODE", file=sys.stderr)


def main() -> int:
    if len(sys.argv) != 2:
        usage()
        return 2

    response_code = sys.argv[1]
    with CSV_FILE.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row["MESH Response Code"] == response_code:
                print(f"Response code: {row['MESH Response Code']}")
                print(f"Response description: {row['MESH Response Description']}")
                print(f"Description: {row['Description']}")
                return 0

    print(f"Response code not found: {response_code}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
