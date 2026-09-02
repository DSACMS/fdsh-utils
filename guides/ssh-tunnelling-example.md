# SSH Tunneling via AWS SSM (Example)

This guide provides one example of how to establish a secure connection to the FDSH Hub Implementation (IMPL) environment from a local development environment.

**Note**: This is just one way to manage tunneling. Your organization may have different security requirements or preferred tools (e.g., VPN, different cloud providers, or alternative proxy methods).

## Overview

Accessing the Hub requires requests to originate from a whitelisted IP. This example uses an SSH tunnel routed through an EC2 instance within a whitelisted AWS NAT Gateway range.

### Architecture

* **Laptop** → **SSH Tunnel (via AWS SSM)** → **EC2 Instance (Whitelisted IP)** → **impl.hub.cms.gov**

## Prerequisites

* **AWS CLI**: [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* **AWS Session Manager Plugin**: [Install Guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
* **AWS Credentials**: Configured via your organization's federated SSO login.
* **SSH Client**: Standard OpenSSH client.

## Setup Instructions

### 1. Configure SSH for SSM

Add the following to your `~/.ssh/config` file to enable SSH over SSM:

```text
Host i-* mi-*
  ProxyCommand sh -c "aws ssm start-session --profile nonprod --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"
  User ec2-user
```

### 2. Establish the SSH Tunnel

Open a tunnel from your local port `8443` to the Hub endpoint. Replace `<INSTANCE_ID>` with your whitelisted EC2 instance ID.

```bash
# Example instance ID: i-0bc4dcef94794e1eb
ssh -L 8443:impl.hub.cms.gov:443 -N -f <INSTANCE_ID>
```

* `-L 8443:impl.hub.cms.gov:443`: Forwards `localhost:8443` to the Hub via the EC2 proxy.
* `-N`: Do not execute remote commands.
* `-f`: Run the process in the background.

### 3. Closing the Tunnel

To close the tunnel later:

```bash
pkill -f "L 8443:impl.hub.cms.gov"
```

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `ssh: connect to host error` | Incorrect Instance ID or instance stopped. | Verify Instance ID and status in AWS Console. |
| Tunnel request hangs | AWS credentials expired or SSM plugin missing. | Refresh AWS SSO login and verify plugin installation. |
