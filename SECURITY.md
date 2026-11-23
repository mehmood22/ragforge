# Security policy

## Supported versions

RAGForge is in early development. Security fixes are intended for the latest development version and latest release; older versions are not guaranteed support.

## Reporting vulnerabilities

Do not open a public issue containing exploit details, credentials or private documents. Use the repository's Security tab → Report a vulnerability if private vulnerability reporting is enabled. If unavailable, seek a private contact method on the maintainer's GitHub profile before sharing details.

Include the affected version or commit, impact, minimal reproduction using synthetic data, and suggested mitigation if available. Allow reasonable time for investigation before public disclosure. No response-time SLA or bounty is promised.

## Deployment considerations

The local Docker setup is not a hardened public deployment. Before exposing it publicly, review TLS, secrets, rate limits, quotas, container privileges, database and vector-store access, backups, monitoring and retention. Treat uploaded content as untrusted. Prompt constraints are not a guarantee against prompt injection. Review external model-provider data handling before uploading sensitive content.
