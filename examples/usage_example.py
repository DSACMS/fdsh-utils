import json
import os
import sys

import python_gateway


def run_live_test():
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
        "",
        education_enrollment_path=education_path,
    )

    print("Gateway initialized.")

    payload = {
        "personGivenName": "Neil",
        "personSurName": "Martinsen-Burrell",
        "personBirthDate": "1999-01-01",
        "asOfDate": "1900-01-01",
        "termsAcceptedIndicator": True,
    }

    try:
        print("Attempting to get education enrollment...")
        result_dict = gateway.get_education_enrollment_v1(payload)
        print("Success!")
        print(json.dumps(result_dict, indent=2))
    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e)
    except:
        print("Unexpected Error:")
        raise


if __name__ == "__main__":
    run_live_test()
