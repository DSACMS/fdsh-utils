import json
import os
from pathlib import Path
from typing import Any

from app.schemas import NscRequestEnvelope, NscResponse
from fastapi.responses import JSONResponse

NSC_DATA_FILE = Path(os.getenv("NSC_DATA_FILE", "/app/data/records.json"))


def error_response(code: str, text: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "nscResponse": {
                "responseMetadata": {
                    "responseCode": code,
                    "responseText": text,
                }
            }
        },
    )


def read_records(data_file: Path = NSC_DATA_FILE) -> list[dict[str, Any]]:
    try:
        with data_file.open(encoding="utf-8") as file:
            records = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("NSC data file is unavailable or invalid") from error
    if not isinstance(records, list):
        raise RuntimeError("NSC data file must contain a JSON array")
    return records


def request_matches(record_request: dict[str, Any], payload: NscRequestEnvelope) -> bool:
    supplied = payload.nscRequest.model_dump(mode="json", exclude_none=True)
    for field in ("personGivenName", "personSurName", "personBirthDate", "asOfDate"):
        if record_request.get(field) != supplied.get(field):
            return False
    for field in ("personSocialSecurityNumber", "personMiddleName", "previousNames"):
        if field in supplied and record_request.get(field) != supplied[field]:
            return False
    return True


def retrieve(payload: NscRequestEnvelope) -> dict | JSONResponse:
    try:
        records = read_records()
    except RuntimeError as error:
        return error_response("ME500000", str(error), 500)

    for record in records:
        if not isinstance(record, dict):
            continue
        if request_matches(record.get("nscRequest", {}), payload):
            response = record.get("nscResponse")
            if isinstance(response, dict):
                return NscResponse.model_validate({"nscResponse": response}).model_dump(
                    mode="json", exclude_none=True
                )
    return error_response("ME123456", "No matching NSC record found", 404)
