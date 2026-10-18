import json
import os
from pathlib import Path
from typing import Any

from app.response_codes import MESH_RESPONSE_CODES, mesh_response_metadata
from app.schemas import NscRequestEnvelope, NscResponse
from fastapi.responses import JSONResponse

NSC_DATA_FILE = Path(os.getenv("NSC_DATA_FILE", "/app/data/records.json"))


def error_response(code: str, status_code: int, text: str | None = None) -> JSONResponse:
    metadata = mesh_response_metadata(code) if code in MESH_RESPONSE_CODES else {
        "responseCode": code,
        "responseText": text or "",
    }
    return JSONResponse(
        status_code=status_code,
        content={"nscResponse": {"responseMetadata": metadata}},
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
    fields = ("personSocialSecurityNumber", "asOfDate")
    if "personGivenName" in supplied:
        fields = fields + ("personGivenName", "personSurName", "personBirthDate")
    for field in fields:
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
        return error_response("MX005001", 500, str(error))

    for record in records:
        if not isinstance(record, dict):
            continue
        if request_matches(record.get("nscRequest", {}), payload):
            response = record.get("nscResponse")
            if isinstance(response, dict):
                response_metadata = response.pop("responseMetadata", None)
                response_code = (response_metadata or {}).get("responseCode", "MS000000")
                if response_code not in MESH_RESPONSE_CODES:
                    return error_response("MX009999", 500)
                return NscResponse.model_validate({"nscResponse": response}).model_dump(
                    mode="json", exclude_none=True
                )
    return error_response("ME123456", 404, "No matching NSC record found")
