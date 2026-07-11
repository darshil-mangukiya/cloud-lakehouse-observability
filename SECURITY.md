# Security Policy

This project is a local portfolio simulation and does not process real customer data. The included datasets are synthetic.

## Reporting Security Issues

If you find a security concern in this repository, open a private report through GitHub security advisories if available, or contact the repository owner directly.

## Secret Handling

- Do not commit `.env` files.
- Do not commit cloud credentials, database passwords, API tokens, or private keys.
- Use `.env.example` as the only tracked environment reference.

## Data Governance Controls

The project includes:

- PII classification metadata.
- PII scan report.
- Access policy matrix.
- Audit manifest with checksums.
- Release gate and exception workflow.

These controls are designed for portfolio demonstration and should be hardened further before production use.
