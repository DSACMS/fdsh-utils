#!/bin/bash
# Hub usage example using `curl` and `jq`
#
# Assumes the tunneling setup from ../guides/ssh-tunneling-example.md
# where localhost:8443 is tunneled to impl.hub.cms.gov:443
#
# client certificate is in /tmp/client.crt and its private key is in
# /tmp/client.key. OAuth ID and secret are in environment variables

OAUTH_CLIENT_KEY=...
OAUTH_CLIENT_SECRET=...

# get access token from /auth/oauth/v2/token
# The encoded token is in the "access_token" property of the JSON response
ACCESS_TOKEN=$(curl -s \
  --cert ./client.crt \
  --key ./client.key \
  --tlsv1.2 --tls-max 1.2 \
  --resolve "impl.hub.cms.gov:8443:127.0.0.1" \
  -X POST \
  https://impl.hub.cms.gov:8443/auth/oauth/v2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${OAUTH_CLIENT_KEY}&client_secret=${OAUTH_CLIENT_SECRET}" \
| jq -r .access_token)

# call the NSC search API
curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  --cert /tmp/client.crt \
  --key /tmp/client.key \
  --tlsv1.2 --tls-max 1.2 \
  --resolve "impl.hub.cms.gov:8443:127.0.0.1" \
  https://impl.hub.cms.gov:8443/mesh/imp1/NationalStudentClearinghouseService \
  -H "messageID: anything-seems-to-work-here" \
  --json '{"nscRequest": {
             "personGivenName": "Neil",
             "personSurName": "Martinsen-Burrell",
             "asOfDate": "1900-01-01",
             "termsAcceptedIndicator": true,
             "personBirthDate": "1999-01-01"
             }
           }'
