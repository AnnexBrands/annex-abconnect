# Developer experience goals

## Goal for SDK 0.3.0 / ABConnect 8_01

A developer with provisioned staging credentials can install the package, make
a first read-only call, understand the inventory/handling-unit and shipment
model, and migrate a supported legacy call using the published documentation.
Release success includes an installable PyPI package and matching Read the Docs
content, both verified from the same release commit.

## Acceptance measures

| Outcome | Measurement |
|---|---|
| First successful call in 10 minutes | A developer unfamiliar with the SDK follows the quickstart in a clean environment with provisioned credentials; record elapsed time and blockers. Credential provisioning time is excluded. |
| Find a common task in two navigation steps | From the docs home, reach setup, What's New, inventory/handling units, multiple shipments, compatibility, or troubleshooting in at most two clicks. Verify those links in rendered HTML. |
| Examples match the installed release | Every changed public method has a complete example with imports, inputs, a real SDK call, and expected response shape or evidence link. Verify signatures offline and capture safe staging behavior. |
| Migrate without guessing | The compatibility matrix maps every affected legacy SDK entry point to its supported route or adapter, warning, replacement, and evidence. No unclassified affected entry remains at release. |
| Operate on the intended shipment | A two-active-shipment scenario proves an operation targeting A leaves B unchanged and ambiguous mutations require context. |
| Diagnose the common failures | Setup/auth, scope, model validation, API errors, and shipment selection have concrete next steps; an onboarding review can find them. |
| Package and docs agree | PyPI install, artifact version, Git tag/commit, RTD versioned build, and stable docs match. Capture URLs and commit IDs in the release record. |

## 0.3.0 evidence and continuing goals

The automated clean-wheel smoke check completed installation, import/CLI discovery,
and the first authenticated staging read in **2.13 seconds** with provisioned
credentials. An independent first-time developer has not completed a timed study;
the 10-minute human onboarding target remains an ongoing usability measure.

The docs home directly links setup, What's New, migration, and troubleshooting.
The migration guide covers inventory/handling units, explicit shipment identifiers,
rate preview versus saved selection, conflict handling, and compatibility. Generated
endpoint pages show Python/CLI signatures and model fields. Reviewed staging captures
and two-shipment isolation checks accompany the contract tests.

The [compatibility matrix](https://github.com/bmonson-annex/annex-abconnect/blob/main/specs/038-abconnect-8-01/compatibility.md)
classifies affected methods. Removed server contracts fail before HTTP instead of
silently losing fields. Some endpoints have contract/source coverage without live
mutation certification; the [validation report](https://github.com/bmonson-annex/annex-abconnect/blob/main/specs/038-abconnect-8-01/validation.md)
records that boundary and the normal-carrier-cancellation failure.

The maintainer executing the release verifies PyPI installation and the matching
Read the Docs version, stable routing, and release commit using the
[runbook](release-runbook.md). Publication evidence belongs in the GitHub release.
Future DX work includes a first-time developer review and broader carrier/endpoint
live coverage. These goals must not be reported as measured until evidence exists.
