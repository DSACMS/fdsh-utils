"""Check FDSH test cases against their specified responses.

FDSH provides an XLSX file with four sheets. We need to use the requests from
the "Payload 1" sheet and compare the corresponding responses on the "Payload
4" sheet.

"""

import os
import sys

from itertools import islice
from pathlib import Path


from openpyxl.reader.excel import load_workbook

import python_gateway


def _extract_as_dict(worksheet, num_columns):
    """Extract rows from sheet as a dict labeled by num_columns in the first row.

    The key for the dict comes from the column "TestCaseID"
    """
    names = [c.value for c in next(worksheet.rows)[:num_columns]]

    output = {}
    # turn remaining rows into dicts using those column names
    for row in islice(worksheet.rows, 1, None):
        row_dict = dict(zip(names, [c.value for c in row]))
        test_id = row_dict.pop("TestCaseID")
        output[test_id] = row_dict
    return output


def _extract_requests(worksheet):
    """Get the requests from the XLSX sheet."""
    # first row has column names (there's 23 of them)
    return _extract_as_dict(worksheet, num_columns=23)


def _extract_responses(worksheet):
    """Get the requests from the XLSX sheet."""
    # first row has column names (there's 36 of them)
    return _extract_as_dict(worksheet, num_columns=36)


def _unflatten_request(flat_request):
    """Re-construct correctly-shaped request object from flat spreadsheet columns.

    The test cases from the spreadsheet are just a bunch of separate columns,
    but the request is in the form of a dict with nesting for various
    parameters. This method constructs the request from the dict with all
    of the columns together.
    """
    full_request = dict()
    # these fields are always required in the request at the top_level
    for name in ["personGivenName", "personSurName", "asOfDate", "termsAcceptedIndicator"]:
        full_request[name] = flat_request[name]

    # fix type for termsAcceptedIndicator
    full_request["termsAcceptedIndicator"] = full_request["termsAcceptedIndicator"].lower() == "true"

    # include these if non-empty
    for name in ["personMiddleName", "personBirthDate", "personSocialSecurityNumber"]:
        if flat_request[name]:
            full_request[name] = flat_request[name]

    # previousNames will be an array of two- or three-element objects
    previous_names = []
    for i in range(1, 6):
        these_columns = [f"previousNames_personGivenName{i}",
                         f"previousNames_personSurName{i}",
                         f"previousNames_personMiddleName{i}",]
        if any(flat_request[column] for column in these_columns):
            # add another name to previous_names
            this_name_object = dict()
            for column_name in these_columns:
                # actual key needs munging
                request_name = column_name[14:-1]
                this_name_object[request_name] = flat_request[column_name]
            previous_names.append(this_name_object)
    if previous_names:
        full_request["previousNames"] = previous_names

    return full_request


def _unflatten_response(flat_response):
    return flat_response


def _gather_test_cases(filename="MH1-NSC Payloads-09032026_v1.xlsx"):
    """Open the test payloads XLSX file and collect request/response pairs.

    The return is a dict whose keys are the "TestCaseID" from the spreadsheet
    and whose values are tuples of request and response data.
    """
    workbook = load_workbook(Path("test_data") / filename)
    request_sheet = workbook["MH1  - Payload 1"]
    response_sheet = workbook["MH1  - Payload 4"]

    requests = _extract_requests(request_sheet)
    responses = _extract_responses(response_sheet)

    test_cases = {
        test_id: (_unflatten_request(requests[test_id]), _unflatten_response(responses[test_id]))
        for test_id in requests.keys()
        if test_id in responses
    }

    return test_cases


def _create_gateway():
    """Create our NSC gateway object.

    Uses secrets from /tmp/client.crt, /tmp/client.key and 
    environment variables OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET.
    """
    # get OAuth client info from the environment
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")

    if (client_id is None) or (client_secret is None):
        print("Error: could not read OAuth credentials from the environment")
        sys.exit(1)

    # URL information
    base_url = "https://impl.hub.cms.gov/"
    token_path = "/auth/oauth/v2/token"
    education_path = "/mesh/imp1/NationalStudentClearinghouseService"

    gateway = python_gateway.HubGateway(
        base_url,
        token_path,
        client_id,
        client_secret,
        "/tmp/client.crt",
        "/tmp/client.key",
        resolve="impl.hub.cms.gov:8443:127.0.0.1",
        education_enrollment_path=education_path,
    )
    return gateway


def check_test_case(request, response, gateway=None):
    """Check that a request gives the matching response."""
    if gateway is None:
        gateway = _create_gateway()

    # make the request
    print("sending payload", request)
    result = gateway.get_education_enrollment_v1(request, raise_on_error=False)

    print(result)
    # compare result against the anticipated response

def check_test_data():
    """Gather test cases and call the gateway and check the response."""

    test_cases = _gather_test_cases()

    # set up our gateway object and use it for all of the test cases
    gateway = _create_gateway()

    for request, response in test_cases.values():
        check_test_case(request, response, gateway=gateway)


if __name__ == "__main__":
    check_test_data()
