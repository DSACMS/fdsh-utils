from dataclasses import dataclass


@dataclass(frozen=True)
class MeshResponseCode:
    response_description: str
    description: str


MESH_RESPONSE_CODES = {
    "MS000000": MeshResponseCode(
        response_description="Successful",
        description="Request processed successfully and valid response returned.",
    ),
    "ME110010": MeshResponseCode(
        response_description="Authentication or authorization failure",
        description="Request failed due to authentication or authorization issue.",
    ),
    "ME100005": MeshResponseCode(
        response_description="This user does not have the privileges to conduct a search.",
        description="Request failed because the user does not have permission to perform a search.",
    ),
    "ME110020": MeshResponseCode(
        response_description="personSocialSecurityNumber is invalid",
        description="Request failed due to an issue with the SSN provided.",
    ),
    "ME110030": MeshResponseCode(
        response_description="personSurName is required or invalid",
        description="Request failed due to an issue with the last name provided.",
    ),
    "ME110040": MeshResponseCode(
        response_description="personGivenName is required or invalid",
        description="Request failed due to an issue with the first name provided.",
    ),
    "ME110050": MeshResponseCode(
        response_description="personMiddleName is invalid",
        description="Request failed due to an issue with the middle name provided.",
    ),
    "ME110060": MeshResponseCode(
        response_description="personBirthDate is invalid",
        description="Request failed due to an issue with the date of birth provided.",
    ),
    "ME110075": MeshResponseCode(
        response_description="asOfDate is invalid",
        description="Request failed due to an issue with the as-of date provided.",
    ),
    "ME120030": MeshResponseCode(
        response_description="previousNames.personGivenName is required or invalid",
        description="Request failed due to an issue with the previous first name provided.",
    ),
    "ME120040": MeshResponseCode(
        response_description="previousNames.personSurName is required or invalid",
        description="Request failed due to an issue with the previous last name provided.",
    ),
    "ME120045": MeshResponseCode(
        response_description="previousNames.personMiddleName is invalid",
        description="Request failed due to an issue with the previous middle name provided.",
    ),
    "MX005001": MeshResponseCode(
        response_description="Unexpected Exception Occurred at Trusted Data Source",
        description="Error occurred while retrieving data from the trusted upstream data source.",
    ),
    "MX009000": MeshResponseCode(
        response_description="Unexpected System Exception",
        description="System-level error occurred; request could not be completed.",
    ),
    "ME007000": MeshResponseCode(
        response_description="Schema Validation Failure",
        description="Request failed due to incorrect request structure or format.",
    ),
    "MX009999": MeshResponseCode(
        response_description="Unexpected Response Code",
        description="Service returned an unknown or unsupported response code.",
    ),
}


def mesh_response_metadata(code: str) -> dict[str, str]:
    response = MESH_RESPONSE_CODES[code]
    return {
        "responseCode": code,
        "responseText": response.response_description,
        "tdsResponseText": response.description,
    }
