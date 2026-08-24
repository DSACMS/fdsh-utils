# Navigating Initial FDSH Hub Connections

This guide assists external developers with the initial technical setup, testing, and integration of Federal Data Services Hub (FDSH) endpoints, specifically focusing on NSC and VA services.

## Table of Contents

* [External Documentation](#external-documentation)
* [Initial Setup Requirements](#initial-setup-requirements)
* [Working Locally and in the Test Environment](#working-locally-and-in-the-test-environment)
* [JWT Token Specification](#jwt-token-specification)

## Prerequisites and Recommended Reading

Before beginning the technical integration, ensure you have reviewed the following foundational documentation:

### External Documentation
* **CMS zONE Hub Onboarding**: Detailed documentation on the administrative process for requesting access, providing IP ranges, and SSL certificate submission.
* **OAuth 2.0 Boarding Guide**: The official CMS guide for OAuth 2.0 integration (available on zONE).
* **HUB Testing Cheat Sheet**: A reference guide for testing Hub connections, including checks for `HubConnectivityService`.
* **HubConnectivityService BSD**: The Business Service Definition (BSD) for the Hub Connectivity Service, which provides the technical specification for connectivity health checks.

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

Accessing the Hub requires all requests to originate from a whitelisted IP address. For local development, this typically involves routing traffic through a whitelisted gateway (e.g., an EC2 instance in a whitelisted AWS NAT Gateway range).

### Authentication Architecture

* **Laptop** → **SSH Tunnel (via AWS SSM)** → **EC2 Instance (Whitelisted IP)** → **impl.hub.cms.gov**

You should never attempt to connect directly to the Hub from a non-whitelisted local environment. Instead, use a tunnel to proxy your requests.

### Prerequisites

* **AWS CLI**: [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* **AWS Session Manager Plugin**: [Install Guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
* **AWS Credentials**: Configured via your organization's federated SSO login.
* **curl**: Standard utility for making HTTP requests.
* **AWS Secrets Manager Access**: Permissions to retrieve `/fdsh/mesh/impl/credentials`.

## Step-by-Step Integration

### Step 1: Retrieve Credentials

The Hub requires a client certificate for mTLS and OAuth client credentials for token requests. These are stored in AWS Secrets Manager.

```bash
# Retrieve the full secret
SECRET=$(aws secretsmanager get-secret-value \
  --secret-id /fdsh/mesh/impl/credentials \
  --query SecretString \
  --output text)

# Save the client certificate and private key
echo "$SECRET" | python3 -c "import sys,json; print(json.load(sys.stdin)['cert'])" > client.crt
echo "$SECRET" | python3 -c "import sys,json; print(json.load(sys.stdin)['certKey'])" > client.key
chmod 600 client.key

# Set OAuth credentials as environment variables
export OAUTH_CLIENT_KEY=$(echo "$SECRET" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientKey'])")
export OAUTH_CLIENT_SECRET=$(echo "$SECRET" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientSecret'])")
```

### Step 2: Configure SSH for SSM

Add the following to your `~/.ssh/config` file to enable SSH over SSM:

```text
Host i-* mi-*
  ProxyCommand sh -c "aws ssm start-session --profile nonprod --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"
  User ec2-user
```

### Step 3: Establish the SSH Tunnel

Open a tunnel from your local port `8443` to the Hub endpoint. Replace `<INSTANCE_ID>` with your whitelisted EC2 instance ID.

```bash
# Example instance ID: i-0bc4dcef94794e1eb
ssh -L 8443:impl.hub.cms.gov:443 -N -f <INSTANCE_ID>
```

* `-L 8443:impl.hub.cms.gov:443`: Forwards `localhost:8443` to the Hub via the EC2 proxy.
* `-N`: Do not execute remote commands.
* `-f`: Run the process in the background.

To close the tunnel later:
```bash
pkill -f "L 8443:impl.hub.cms.gov"
```

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

A successful request returns a JSON Web Token (JWT). Below is a sample payload:

```json
{
  "iss": "https://test.hub.cms.gov:443",
  "iat": 1629764946,
  "aud": "XXXXXXXXXX",
  "exp": 1629768546,
  "jti": "XXXXXXXXXXXX",
  "token_details": {
    "scope": "RJ74 RJ03",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

#### Field Definitions

| Field | Description |
| :--- | :--- |
| `iss` | **Issuer**: The URL of the server that issued the token. |
| `iat` | **Issued At**: The Unix timestamp indicating when the token was generated. |
| `aud` | **Audience**: The intended recipient of the token (your Client ID). |
| `exp` | **Expiration**: The Unix timestamp indicating when the token expires. |
| `jti` | **JWT ID**: A unique identifier for the token to prevent replay attacks. |
| `token_details.scope` | The permissions (scopes) granted to this token. |
| `token_details.expires_in` | The remaining lifetime of the token in seconds (typically 3600). |
| `token_details.token_type` | The type of token issued (e.g., "Bearer"). |

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `ssh: connect to host error` | Incorrect Instance ID or instance stopped. | Verify Instance ID and status in AWS Console. |
| `curl: (35) SSL handshake failed` | Certificate/Key mismatch or expired. | Re-pull credentials from Secrets Manager. |
| `{"error":"invalid_client"}` | Invalid OAuth credentials. | Re-pull credentials and verify environment variables. |
| Token request hangs | SSH Tunnel is not active. | Re-establish the tunnel using the `ssh -L` command. |
| `AccessDeniedException` | Insufficient IAM permissions. | Request `secretsmanager:GetSecretValue` for the credential path. |

## Security Reminders

* **Never commit certificates (`.crt`) or private keys (`.key`)** to version control.
* **Never share your OAuth token**; it is scoped to your specific session.
* **Restrict file permissions**: Ensure `client.key` is only readable by your user (`chmod 600`).
* **Credential Rotation**: Credentials in Secrets Manager are rotated periodically. If you encounter authentication errors, re-pull the latest credentials.
