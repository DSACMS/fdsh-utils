import csv
from pathlib import Path

import jwt
import pytest
from app.domains.nsc import read_records
from app.main import app
from app.schemas import NscResponse
from app.security import issue_token, settings
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

FEATURES = Path(__file__).resolve().parents[1] / "features"
RESPONSE_CODES = Path(__file__).resolve().parents[1] / "mesh_response_codes.csv"

scenarios(str(FEATURES))


@pytest.fixture
def request_context():
    return {
        "payload": {
            "nscRequest": {
                "personGivenName": "Casey",
                "personSurName": "Bennett",
                "personBirthDate": "1966-06-07",
                "asOfDate": "2023-10-13",
                "termsAcceptedIndicator": True,
            }
        }
    }


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def response_code_record(response_code: str) -> dict[str, str]:
    with RESPONSE_CODES.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row["MESH Response Code"] == response_code:
                return row
    raise AssertionError(f"Response code {response_code} is missing from {RESPONSE_CODES}")


def expected_status(response_code: str) -> int:
    if response_code == "MS000000":
        return 200
    if response_code in {"ME110010", "ME100005"}:
        return 401 if response_code == "ME110010" else 403
    if response_code.startswith("ME"):
        return 422
    return 500


def set_request_field(request_context: dict, field: str, value):
    request_context["payload"]["nscRequest"][field] = value


@given("the NSC request is valid and a matching record exists")
def valid_matching_request(request_context):
    request_context["payload"] = {"nscRequest": read_records()[0]["nscRequest"]}
    return request_context


@given("the request has an authentication or authorization failure")
def authentication_failure_request(request_context):
    request_context["headers"] = {}
    return request_context


@given("the authenticated user does not have privileges to conduct a search")
def search_privilege_failure_request(request_context):
    request_context["headers"] = {
        "Authorization": "Bearer "
        + jwt.encode(
            {"sub": "local-dev-client-id", "scope": "nsc:write"},
            settings.jwt_signing_key,
            algorithm="HS256",
        )
    }
    return request_context


@given("the NSC request contains an invalid personSocialSecurityNumber")
def invalid_ssn_request(request_context):
    set_request_field(request_context, "personSocialSecurityNumber", "0000")
    return request_context


@given("the NSC request has a missing or invalid personSurName")
def invalid_surname_request(request_context):
    set_request_field(request_context, "personSurName", "")
    return request_context


@given("the NSC request has a missing or invalid personGivenName")
def invalid_given_name_request(request_context):
    set_request_field(request_context, "personGivenName", "")
    return request_context


@given("the NSC request contains an invalid personMiddleName")
def invalid_middle_name_request(request_context):
    set_request_field(request_context, "personMiddleName", "")
    return request_context


@given("the NSC request contains an invalid personBirthDate")
def invalid_birth_date_request(request_context):
    set_request_field(request_context, "personBirthDate", "not-a-date")
    return request_context


@given("the NSC request contains an invalid asOfDate")
def invalid_as_of_date_request(request_context):
    set_request_field(request_context, "asOfDate", "not-a-date")
    return request_context


@given("the NSC request contains an invalid previousNames.personGivenName")
def invalid_previous_given_name_request(request_context):
    request_context["payload"]["nscRequest"]["previousNames"] = [
        {"personGivenName": "", "personSurName": "Owens"}
    ]
    return request_context


@given("the NSC request contains an invalid previousNames.personSurName")
def invalid_previous_surname_request(request_context):
    request_context["payload"]["nscRequest"]["previousNames"] = [
        {"personGivenName": "Jordan", "personSurName": ""}
    ]
    return request_context


@given("the NSC request contains an invalid previousNames.personMiddleName")
def invalid_previous_middle_name_request(request_context):
    request_context["payload"]["nscRequest"]["previousNames"] = [
        {
            "personGivenName": "Jordan",
            "personSurName": "Owens",
            "personMiddleName": "",
        }
    ]
    return request_context


@given("the NSC request fails schema validation")
def schema_failure_request(request_context):
    request_context["payload"] = {"unexpected": True}
    return request_context


@given("the trusted data source raises an unexpected exception while retrieving data")
def trusted_data_source_failure_request(request_context, monkeypatch):
    from app.domains import nsc

    def raise_data_source_error():
        raise RuntimeError("simulated trusted data source failure")

    monkeypatch.setattr(nsc, "read_records", raise_data_source_error)
    return request_context


@given("the mock service encounters an unexpected system exception")
def system_failure_request(request_context):
    from app import main

    def raise_system_error(_payload):
        raise RuntimeError("simulated system failure")

    request_context["headers"] = {
        "Authorization": f"Bearer {issue_token('local-dev-client-id')['access_token']}"
    }
    main.retrieve_nsc = raise_system_error
    return request_context


@given("the trusted service returns an unknown or unsupported response code")
def unexpected_response_code_request(request_context, monkeypatch):
    from app.domains import nsc

    monkeypatch.setattr(
        nsc,
        "read_records",
        lambda: [
            {
                "nscRequest": request_context["payload"]["nscRequest"],
                "nscResponse": {
                    "responseMetadata": {
                        "responseCode": "ZZ999999",
                        "responseText": "Unsupported",
                    }
                },
            }
        ],
    )
    return request_context


@when("the client submits the request to the NSC retrieve endpoint")
def submit_request(client, request_context):
    headers = request_context.get("headers")
    if headers is None:
        headers = {
            "Authorization": f"Bearer {issue_token('local-dev-client-id')['access_token']}"
        }
    request_context["response"] = client.post(
        "/mesh/imp1/NationalStudentClearinghouseService",
        json=request_context["payload"],
        headers=headers,
    )


@then(parsers.parse('the response code is "{response_code}"'))
def assert_response_code(request_context, response_code):
    response = request_context["response"]
    assert response.status_code == expected_status(response_code)
    metadata = response.json()["nscResponse"]["responseMetadata"]
    assert metadata["responseCode"] == response_code
    expected = response_code_record(response_code)
    assert metadata["responseText"] == expected["MESH Response Description"]
    if expected["Description"]:
        assert metadata["tdsResponseText"] == expected["Description"]


@then("the successful response matches the NSC response schema")
def assert_success_response_schema(request_context):
    NscResponse.model_validate(request_context["response"].json())


@then(parsers.parse('the response description is "{response_description}"'))
def assert_response_description(request_context, response_description):
    metadata = request_context["response"].json()["nscResponse"]["responseMetadata"]
    assert metadata["responseText"] == response_description
