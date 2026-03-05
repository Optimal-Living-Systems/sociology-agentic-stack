# Security Baseline

This baseline defines minimum controls for the OLS sociology stack.

## 1) Secrets Handling

- Never commit `.env` or real API keys to git.
- Keep `.env.example` placeholders only.
- Rotate keys if accidental exposure is detected.
- Restrict secrets to least privilege per provider/project.

## 2) Network and Service Exposure

- Bind local services (Langfuse, LiteLLM, databases) to localhost by default.
- Expose externally only behind authenticated gateway/reverse proxy.
- Enforce TLS for remote access paths.

## 3) Review Safety Posture

- Review tooling is read-only by default.
- Disable any auto-fix or unsafe agent execution mode.
- Persist review findings to reports; human decides remediation.

## 4) Dependency Hygiene

- Install from pinned/locked dependency set.
- Run vulnerability scans before public releases.
- Track breaking API changes for model SDK dependencies.

## 5) Data Governance

- Treat corpus and generated artifacts as sensitive until classified.
- Strip personally identifying details from shared examples.
- Log source provenance for every generated claim.

## 6) Access Control

- Separate developer and operator credentials.
- Use project-scoped keys for Langfuse and LLM providers.
- Audit who can trigger flows and modify templates.

## 7) Incident Response Baseline

- Keep immutable logs for orchestration and review runs.
- Define key rotation and rollback procedures.
- Document and test restore from archived artifacts.

## 8) Security TODOs

- [TODO][Phase B2] Add secret scanning in CI.
- [TODO][Phase B3] Add signed release and SBOM generation.
- [TODO][Phase C1] Add policy-as-code checks for runtime configs.
