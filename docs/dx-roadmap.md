# Developer experience goals

## Goal for SDK 0.3.0 / ABConnect 8_01

A developer with provisioned staging credentials can install the package, make
a first read-only call, understand the inventory/handling-unit and shipment
model, and migrate a supported legacy call using the published documentation.
Release success includes an installable PyPI package and matching Read the Docs
content, both verified from the same release commit.

## Acceptance measures

| Outcome | Release acceptance evidence |
|---|---|
| First successful call in 10 minutes | A developer unfamiliar with the SDK follows the quickstart in a clean environment with provisioned credentials; record elapsed time and blockers. Credential provisioning time is excluded. |
| Find a common task in two navigation steps | From the docs home, reach setup, What's New, inventory/handling units, multiple shipments, compatibility, or troubleshooting in at most two clicks. Verify those links in rendered HTML. |
| Examples match the installed release | Every changed public method has a complete example with imports, inputs, a real SDK call, and expected response shape or evidence link. Verify signatures offline and capture safe staging behavior. |
| Migrate without guessing | The compatibility matrix maps every affected legacy SDK entry point to its supported route or adapter, warning, replacement, and evidence. No unclassified affected entry remains at release. |
| Operate on the intended shipment | A two-active-shipment scenario proves an operation targeting A leaves B unchanged and ambiguous mutations require context. |
| Diagnose the common failures | Setup/auth, scope, model validation, API errors, and shipment selection have concrete next steps; an onboarding review can find them. |
| Package and docs agree | PyPI install, artifact version, Git tag/commit, RTD versioned build, and stable docs match. Capture URLs and commit IDs in the release record. |

These are targets, not completed usability or live-API measurements.

## Work and current status

- **Prepared locally:** a task-oriented docs home, package-install quickstart,
  corrected call signatures, What's New, a migration preview, troubleshooting,
  and a publication runbook with both delivery destinations.
- **Before release:** implement the 8_01 API surface, complete canonical and
  compatibility examples, capture fixtures and shipment-isolation evidence,
  perform the timed onboarding review, and replace the migration preview.
- **Deployment prerequisite:** synchronize `main` and release tags to the
  AnnexBrands upstream used by RTD, then verify builds and version routing as
  described in the runbook.

The maintainer executing the release owns the evidence checklist. Detailed
implementation belongs to the next FR/speckit round. The
[release scope](https://github.com/bmonson-annex/annex-abconnect/tree/main/specs/038-abconnect-8-01)
defines the required API behavior; the [runbook](release-runbook.md) defines
publication and verification.
