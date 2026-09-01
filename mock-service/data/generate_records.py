#!/usr/bin/env python3
"""
Generate synthetic NSC records for the read-only mock-service image.

python3 data/generate_records.py \
  --count 100 \
  --output data/records.json

reproducible output:
python3 data/generate_records.py \
  --count 100 \
  --output data/test-records.json \
  --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

FIRST_NAMES = (
    "Avery", "Blake", "Casey", "Dakota", "Emerson", "Jordan", "Morgan", "Riley",
    "Harper", "Quinn", "Sage", "Rowan", "Finley", "Peyton", "Reese", "Kai",
    "Tatum", "Noah", "Mila", "Luca", "Willow", "Eli", "Nora", "Owen",
)
LAST_NAMES = (
    "Carter", "Ellis", "Hayes", "Jordan", "Parker", "Reed", "Rivera", "Taylor",
    "Bennett", "Brooks", "Foster", "Gray", "Morris", "Nolan", "Owens", "Phelps",
    "Sutton", "Vega", "West", "Young", "Adams", "Baker", "Collins", "Davis",
)
SCHOOL_NAMES = (
    "Example State University", "North Valley College", "Lakeside Institute",
    "Pine Ridge University", "Cedar Grove College", "Summit Technical School",
)
ENROLLMENT_STATUSES = ("F", "Q", "H", "L", "Y", "A", "W", "S", "G", "D")


def random_date(rng: random.Random, start: date, end: date) -> str:
    return (start + timedelta(days=rng.randint(0, (end - start).days))).isoformat()


def random_ssn(rng: random.Random) -> str:
    area = rng.choice([value for value in range(100, 600) if value != 666])
    group = rng.randint(10, 99)
    serial = rng.randint(1, 9999)
    return f"{area:03d}{group:02d}{serial:04d}"


def previous_name(rng: random.Random) -> dict[str, str]:
    value = {
        "personGivenName": rng.choice(FIRST_NAMES),
        "personSurName": rng.choice(LAST_NAMES),
    }
    if rng.random() < 0.5:
        value["personMiddleName"] = rng.choice(FIRST_NAMES)
    return value


def build_record(rng: random.Random, record_number: int) -> dict:
    given_name = rng.choice(FIRST_NAMES)
    surname = rng.choice(LAST_NAMES)
    birth_date = random_date(rng, date(1950, 1, 1), date(2005, 12, 31))
    as_of_date = random_date(rng, date(2020, 1, 1), date(2026, 12, 31))
    include_optional = record_number % 2 == 0

    request = {
        "personGivenName": given_name,
        "personSurName": surname,
        "personBirthDate": birth_date,
        "asOfDate": as_of_date,
        "termsAcceptedIndicator": True,
    }
    if include_optional:
        request["personSocialSecurityNumber"] = random_ssn(rng)
        request["personMiddleName"] = rng.choice(FIRST_NAMES)
        request["previousNames"] = [previous_name(rng) for _ in range(rng.randint(1, 3))]

    student_info = {
        "personGivenName": given_name,
        "personSurName": surname,
        "personBirthDate": birth_date,
    }
    if include_optional:
        student_info["personMiddleName"] = request["personMiddleName"]
        student_info["previousNames"] = request["previousNames"]

    response = {
        "transactionDetails": {
            "transactionId": f"{4000000000 + record_number:010d}",
            "orderId": f"{2000000000 + record_number:010d}",
            "transactionStatusCode": "CNF",
            "transactionFee": "0.00",
            "salesTax": "0.00",
            "transactionTotal": "0.00",
            "requestedByText": f"Seed Data {record_number:04d}",
            "requestedDateTimeText": "2026-08-24 09:00:00.000",
            "nscHitIndicator": True,
        },
        "studentInfoProvided": student_info,
        "enrollmentDetails": {
            "officialSchoolName": rng.choice(SCHOOL_NAMES),
            "schoolCode": f"{3790 + (record_number % 1000):06d}",
            "branchCode": f"{record_number % 100:02d}",
            "currentEnrollmentStatusCode": "CC" if record_number % 3 else "CN",
            "enrollmentData": {
                "enrollmentStatusCode": rng.choice(ENROLLMENT_STATUSES),
                "termBeginDate": "2025-08-25",
                "termEndDate": "2025-12-19",
                "schoolCertifiedOnDate": "2025-12-12",
            },
        },
        "responseMetadata": {
            "responseCode": "MS000000",
            "responseText": "Success",
        },
    }
    if include_optional:
        response["transactionDetails"]["notifiedDateTimeText"] = "2026-08-24 09:00:01.000"
        response["enrollmentDetails"]["enrollmentData"]["anticipatedGraduationDate"] = "2027-05-17"

    return {"nscRequest": request, "nscResponse": response}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, required=True, help="Number of records to create.")
    parser.add_argument("--output", type=Path, required=True, help="JSON file to write.")
    parser.add_argument("--seed", type=int, help="Optional seed for reproducible output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.count < 1:
        raise SystemExit("--count must be at least 1")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    records = [build_record(rng, number) for number in range(1, args.count + 1)]
    args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
