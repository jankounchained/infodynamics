---
phase: 05
slug: verify
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-07-14
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| user code → optional-dependency import | A caller without the `morphology` extra crosses into `MorphologicalEncoder.encode()`; only the failure-mode error message changes (05-01). | Error message text |
| (none new) | 05-02 runs read-only verification checks and authors a planning-metadata doc; no endpoint, no user-input path, no new dependency (05-02). | N/A |
| CI runner ← third-party GitHub Actions | Marketplace Actions (`actions/checkout`, `actions/setup-python`) execute code inside the CI runner (05-03). | Workflow execution |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-01 | Information Disclosure (under-disclosure) | `MorphologicalEncoder` optional-import guards, `infodynamics/text/morphology.py` | low | mitigate | Bare `ModuleNotFoundError` replaced with actionable `ImportError` naming the `morphology` extra + `pip install infodynamics[morphology]`, applied consistently at all 4 guard sites (lines 41, 48, 114, 196). | closed |
| T-05-02 | (no applicable STRIDE category) | Verification/audit + doc authoring | low | accept | No new attack surface — read-only verification pass over already-shipped code; nothing to mitigate. | closed |
| T-05-03 | Tampering (supply chain) | `.github/workflows/ci.yml` third-party Action references | high | mitigate | `actions/checkout` and `actions/setup-python` pinned to immutable major-version tags (`@v7`, `@v6`), not `@main`/`@master`. | closed |
| T-05-04 | Elevation of Privilege | `GITHUB_TOKEN` permissions in `.github/workflows/ci.yml` | low | mitigate | No `permissions:` block added — workflow runs under GitHub Actions' restrictive default read-only token; no `contents: write`, no publish/deploy steps. | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-05-01 | T-05-02 | Read-only verification/doc-authoring pass over already-shipped code introduces no new attack surface; ASVS V2/V3/V4/V5/V6/V14 all N/A. | gsd-secure-phase (retroactive, plan-time disposition) | 2026-07-14 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-14 | 4 | 4 | 0 | gsd-secure-phase (L1 grep-depth, register authored at plan time) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-14
