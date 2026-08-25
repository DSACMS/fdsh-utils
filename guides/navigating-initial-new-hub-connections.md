# Navigating Initial FDSH Hub Connections

This guide assists external developers with the initial technical setup, testing, and integration of Federal Data Services Hub (FDSH) endpoints, specifically focusing on NSC and VA services.

## Table of Contents

* [External Documentation](#external-documentation)
* [Initial Setup Requirements](#initial-setup-requirements)
* [Working Locally and in the Test Environment](#working-locally-and-in-the-test-environment)
* [JWT Token Specification](#jwt-token-specification)
* [Example: SSH Tunneling via AWS SSM](./ssh-tunnelling-example.md)

## Prerequisites and Recommended Reading

Before beginning the technical integration, ensure you have reviewed the following foundational documentation:

### External Documentation
* **CMS zONE Hub Onboarding**: Detailed documentation on the administrative process for requesting access, providing IP ranges, and SSL certificate submission.
* **OAuth 2.0 Boarding Guide**: The official CMS guide for OAuth 2.0 integration (available on zONE).
* **HUB Testing Cheat Sheet**: A reference guide for testing Hub connections, including checks for `HubConnectivityService`.
* **HubConnectivityService BSD**: The Business Service Definition (BSD) for the Hub Connectivity Service, which provides the technical specification for connectivity health checks.
* **Formal Environment Testing URL End Points**: Lists the URLs that are used for testing the Hub's Implementation (IMPL) environment.

### Repository Documentation
* [**Project README**](../README.md): Overview of the `fdsh-utils` project and its core goals.
* [**MEDH NSC Service Specifications**](../specs/medh/nsc/README.md): Detailed OpenAPI and JSON Schema specifications for the NSC endpoint.
* [**Security Policy**](../SECURITY.md): Guidelines for vulnerability reporting and sensitive data handling.

## Initial Setup Requirements

To establish a connection to the Hub's Implementation (IMPL) environment, you must first complete the onboarding process:
1. **IP Whitelisting**: Provide your outbound IP ranges to the Hub team.
2. **SSL Certificates**: Submit your public SSL certificates to the Hub for mTLS authentication.

This guide assumes you have already completed these administrative steps and possess the necessary credentials.

## Working Locally and in the Test Environment

Accessing the Hub requires all requests to originate from a whitelisted IP address. Because local environments are typically not whitelisted, you must route your traffic through a whitelisted gateway.

### Tunnelling and Proxying

There are multiple ways to manage connectivity to the Hub (e.g., corporate VPNs, specialized proxy servers, or cloud-native gateways). For a detailed example of one such method using AWS SSM and SSH, see:

* [**Example: SSH Tunneling via AWS SSM**](./ssh-tunnelling-example.md)

This example is provided for reference only; your specific infrastructure may require a different approach.

### Prerequisites

* **curl**: Standard utility for making HTTP requests.
* **jq**: Standard utility for parsing JSON.
* **aws**: Standard utility for aws command line (if you are using AWS to manage credentials).

## Step-by-Step Integration

### Step 1: Retrieve Credentials

The Hub requires a client certificate for mTLS and OAuth client credentials for token requests. For our walkthrough, we're assuming they are stored in AWS Secrets Manager.

```bash

#import credentials, extract client certificate and key

aws secretsmanager get-secret-value \
  --secret-id /fdsh/mesh/impl/credentials \
  --query SecretString \
  --output text > /tmp/fdsh-mesh-credentials.json

jq -r '.cert' /tmp/fdsh-mesh-credentials.json > client.crt
jq -r '.certKey' /tmp/fdsh-mesh-credentials.json > client.key

chmod 600 client.key

#export credentials

export OAUTH_CLIENT_KEY="$(jq -r '.clientKey' /tmp/fdsh-mesh-credentials.json)"
export OAUTH_CLIENT_SECRET="$(jq -r '.clientSecret' /tmp/fdsh-mesh-credentials.json)"

rm -f /tmp/fdsh-mesh-credentials.json
```

### Step 2: Establish the Connection

Ensure your local environment has a path to the Hub (e.g., via the [SSH Tunneling Example](./ssh-tunnelling-example.md)). The integration steps below assume the Hub is accessible via `localhost:8443`.

## JWT Token Specification

The Hub uses OAuth 2.0 Client Credentials flow. Tokens are requested from the following endpoint:

**Endpoint**: `https://impl.hub.cms.gov:8443/auth/oauth/v2/token`

### Token Request

When using the local tunnel, the request must include the `--resolve` flag to ensure the TLS handshake uses the correct SNI (Server Name Indication).

```bash
curl -s \
  --cert ./client.crt \
  --key ./client.key \
  --tlsv1.2 --tls-max 1.2 \
  --resolve "impl.hub.cms.gov:8443:127.0.0.1" \
  -X POST https://impl.hub.cms.gov:8443/auth/oauth/v2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${OAUTH_CLIENT_KEY}&client_secret=${OAUTH_CLIENT_SECRET}"
```

### JWT Response Payload

A successful request returns an OAuth 2.0 response containing the access token. While the top-level response contains standard OAuth fields, the `access_token` itself is a JWT that contains critical metadata.

#### OAuth 2.0 Response Wrapper
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "scope": "MH-1 MH-2 RJ74"
}
```

#### Decoded JWT Content
When the `access_token` is decoded, it contains the following structure:

```json
{
  "iss": "https://impl.hub.cms.gov:8443",
  "iat": 1787613531,
  "aud": "8e1ce620-d9c6-48ab-9b11-4970dd06551b",
  "exp": 1787615331,
  "refresh_token": "",
  "jti": "0db9a20a-fdf9-40ae-ae74-eab11bcfc516-1787615331",
  "token_details": {
    "scope": "MH-1 MH-2 RJ74",
    "expires_in": 1800,
    "token_type": "Bearer"
  }
}
```

#### Field Definitions (Decoded JWT)

| Field | Description |
| :--- | :--- |
| `iss` | Issuer: The URL of the Hub authentication server. |
| `iat` | Issued At: Epoch timestamp of when the token was generated. |
| `aud` | Audience: The client ID or intended recipient of the token. |
| `exp` | Expiration Time: Epoch timestamp when the token expires. |
| `jti` | JWT ID: A unique identifier for the token. |
| `token_details` | A nested object containing specific token metadata. |
| `token_details.scope` | A space-separated list of permissions (scopes) granted. |
| `token_details.expires_in` | The lifetime of the token in seconds (e.g., 1800). |
| `token_details.token_type` | The type of token issued (always "Bearer"). |

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `curl: (35) SSL handshake failed` | Certificate/Key mismatch or expired. | Re-pull credentials from Secrets Manager. |
| `{"error":"invalid_client"}` | Invalid OAuth credentials. | Re-pull credentials and verify environment variables. |
| Token request hangs | Network path to Hub is not active. | Check your tunnel, VPN, or proxy connection. |
| `AccessDeniedException` | Insufficient IAM permissions. | Request `secretsmanager:GetSecretValue` for the credential path. |

## Security Reminders

* **Never commit certificates (`.crt`) or private keys (`.key`)** to version control.
* **Never share your OAuth token**; it is scoped to your specific session.
* **Restrict file permissions**: Ensure `client.key` is only readable by your user (`chmod 600`).
* **Credential Rotation**: Credentials in Secrets Manager are rotated periodically. If you encounter authentication errors, re-pull the latest credentials.
