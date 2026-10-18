from __future__ import annotations

import json
import logging
import string
from datetime import date
from pathlib import Path

import pytest
from app.domains.nsc import read_records, request_matches, retrieve
from app.schemas import (
  NscRequest,
  NscRequestEnvelope,
  NscResponse,
  PreviousName,
  SsnOnlyVerificationRequest,
)
from app.security import issue_token, settings, verify_token
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

letters = st.text(
    alphabet=string.ascii_letters,
    min_size=1,
    max_size=20,
)
valid_dates = st.dates(min_value=date(1900, 1, 1), max_value=date(2035, 12, 31))
valid_previous_name = st.builds(
    PreviousName,
    personGivenName=letters,
    personMiddleName=st.none() | letters,
    personSurName=letters,
)

# SSN value can be the last 4 digits or the full 9 digits.
# The last 4 digits are always valid if they are in the range 1000-9999.
# The full 9 digits have more complex rules, but we will only test for the basic rules here.
valid_ssn_4 = st.integers(min_value=1000, max_value=9999).map(str)
valid_ssn_9 = (
    st.integers(min_value=100000000, max_value=999999999)
    .map(str)
    .filter(lambda value: not value.startswith(("000", "666", "9")))
)
valid_ssn = st.one_of(valid_ssn_4, valid_ssn_9)

valid_request = st.builds(
    NscRequest,
    personSocialSecurityNumber=st.none() | valid_ssn,
    personGivenName=letters,
    personMiddleName=st.none() | letters,
    personSurName=letters,
    previousNames=st.none() | st.lists(valid_previous_name, min_size=1, max_size=5),
    personBirthDate=valid_dates,
    asOfDate=valid_dates,
    termsAcceptedIndicator=st.just(True),
)


@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=30))
def test_issue_token_uses_supplied_client_id(client_id: str):
    payload = issue_token(client_id)
    assert payload["token_type"] == "Bearer"
    assert payload["expires_in"] == settings.token_ttl_seconds

    claims = verify_token(payload["access_token"])
    assert claims is not None
    assert claims["sub"] == client_id
    assert claims["scope"] == "nsc:read"


@given(st.text())
def test_verify_token_rejects_non_jwt_strings(value: str):
    assert verify_token(value) is None


@given(valid_request)
def test_valid_nsc_request_round_trips(request: NscRequest):
    envelope = NscRequestEnvelope(nscRequest=request)
    assert envelope.nscRequest == request
    assert envelope.model_dump(mode="json")["nscRequest"]["termsAcceptedIndicator"] is True


@given(valid_request)
def test_request_matches_true_for_identical_record(request: NscRequest):
    payload = NscRequestEnvelope(nscRequest=request)
    record = request.model_dump(mode="json", exclude_none=True)

    assert request_matches(record, payload) is True


@given(valid_request)
def test_request_matches_false_for_one_field_difference(request: NscRequest):
    payload = NscRequestEnvelope(nscRequest=request)
    record = request.model_dump(mode="json", exclude_none=True)
    mutated = dict(record)
    mutated["personGivenName"] = "Z" if record["personGivenName"] != "Z" else "Y"

    assert request_matches(mutated, payload) is False


@given(valid_request)
def test_invalid_ssn_is_rejected(request: NscRequest):
    invalid_ssn = "0000"
    with pytest.raises(ValidationError):
        NscRequest.model_validate(
            {
                **request.model_dump(mode="json", exclude_none=True),
                "personSocialSecurityNumber": invalid_ssn,
            }
        )


@given(valid_request)
def test_invalid_terms_flag_is_rejected(request: NscRequest):
    with pytest.raises(ValidationError):
        NscRequest.model_validate(
            {
                **request.model_dump(mode="json", exclude_none=True),
                "termsAcceptedIndicator": False,
            }
        )


@given(valid_request)
def test_response_models_accept_valid_success_payload(request: NscRequest):
    success_payload = {
        "nscResponse": {
            "transactionDetails": {
                "transactionId": "4000000009",
                "orderId": "2000000009",
                "transactionStatusCode": "CNF",
                "transactionFee": "0.00",
                "salesTax": "0.00",
                "transactionTotal": "0.00",
                "requestedByText": "Seed Data 0009",
                "requestedDateTimeText": "2026-08-24 09:00:00.000",
                "nscHitIndicator": True,
            },
            "studentInfoProvided": {
                "personGivenName": request.personGivenName,
                "personSurName": request.personSurName,
                "personBirthDate": request.personBirthDate,
            },
                "enrollmentDetails": [{
                "officialSchoolName": "Sample School",
                "schoolCode": "003791",
                "branchCode": "01",
                "currentEnrollmentStatusCode": "CC",
                    "enrollmentData": [{
                    "enrollmentStatusCode": "Q",
                    "termBeginDate": date(2025, 8, 25),
                    "termEndDate": date(2025, 12, 19),
                    "schoolCertifiedOnDate": date(2025, 12, 12),
                    }],
                }],
        }
    }

    model = NscResponse.model_validate(success_payload)
    assert model.nscResponse.enrollmentDetails[0].enrollmentData[0].enrollmentStatusCode == "Q"


def test_ssn_only_request_is_accepted():
    request = NscRequestEnvelope.model_validate({
        "nscRequest": {
            "personSocialSecurityNumber": "123456789",
            "asOfDate": "2026-01-01",
            "termsAcceptedIndicator": True,
        }
    })

    assert isinstance(request.nscRequest, SsnOnlyVerificationRequest)


@given(valid_request)
def test_response_models_accept_valid_error_payload(request: NscRequest):
    payload = {
        "nscResponse": {
            "responseMetadata": {
                "responseCode": "ME123456",
                "responseText": "No matching NSC record found",
            }
        }
    }

    model = NscResponse.model_validate(payload)
    assert model.nscResponse.responseMetadata.responseCode == "ME123456"


def test_read_records_works_with_seed_dataset():
    records = read_records()

    assert isinstance(records, list)
    assert len(records) >= 1
    assert all(isinstance(record, dict) for record in records)


def test_read_records_rejects_invalid_json_file(tmp_path):
    invalid_file = tmp_path / "test_records.json"
    invalid_file.write_text("{not valid json}", encoding="utf-8")

    with pytest.raises(RuntimeError, match="unavailable or invalid"):
        read_records(invalid_file)


def test_retrieve_returns_matching_seed_record():
    record = read_records()[0]
    payload = NscRequestEnvelope.model_validate(
        {"nscRequest": record["nscRequest"]}
    )

    result = retrieve(payload)
    assert isinstance(result, dict)
    assert result["nscResponse"]["transactionDetails"]["transactionStatusCode"] == "CNF"


def test_retrieve_returns_404_for_missing_record():
    payload = NscRequestEnvelope.model_validate(
        {
            "nscRequest": {
                "personGivenName": "Definitely",
                "personSurName": "NotPresent",
                "personBirthDate": "1999-01-01",
                "asOfDate": "2023-10-13",
                "termsAcceptedIndicator": True,
            }
        }
    )

    result = retrieve(payload)
    assert hasattr(result, "status_code")
    assert result.status_code == 404


def test_read_records_file_must_be_array(tmp_path):
    bad_file = tmp_path / "test_records.json"
    bad_file.write_text(json.dumps({"not": "a-list"}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="must contain a JSON array"):
        read_records(bad_file)
