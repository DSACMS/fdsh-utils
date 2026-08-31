
"""
Run tests of the FDSH NSC API.

When run without arguments, `python3 usage_example.py`, this script creates a
connection to the FDSH using the details given in the code, then calls the
API for a sample user and prints the results.

This same script can also read newline-delimited JSON payloads from stdin to allow
for querying the API multiple times. E.g. `python3 usage_example.py < nsc_sample_users.json`
"""

import io
import json
import os
import sys

import requests

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
        resolve="impl.hub.cms.gov:8443:127.0.0.1",
        education_enrollment_path=education_path,
    )

    print("Gateway initialized.")

    if sys.stdin.isatty():
        print("Searching for sample individuals...")
        payload = {
            "personGivenName": "Teresa",
            "personSurName": "Kaminsky",
            "personBirthDate": "1994-06-20",
            "asOfDate": "2026-08-27",
            "termsAcceptedIndicator": True,
        }
        input_stream = io.StringIO(json.dumps(payload) + "\n")
    else:
        print("Searching for individuals from stdin...")
        input_stream = sys.stdin

    for line in input_stream:
        payload = json.loads(line)
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
