# Release runbook

A release is complete only when its package is available from **PyPI** and its
matching version is built and visible on **Read the Docs**. A GitHub release or
a green package-upload job alone is insufficient.

Run this procedure after implementation and validation. Record publication
evidence separately from local checks.

## Destinations and repository

| Item | Location |
|---|---|
| Source and release tags | [bmonson-annex/annex-abconnect](https://github.com/bmonson-annex/annex-abconnect) |
| Documentation upstream | [AnnexBrands/annex-abconnect](https://github.com/AnnexBrands/annex-abconnect) |
| PyPI distribution | [annex-abconnect](https://pypi.org/project/annex-abconnect/) |
| Python import | `ab` |
| Documentation project | [ab-sdk](https://app.readthedocs.org/projects/ab-sdk/) |
| Development docs | [latest](https://ab-sdk.readthedocs.io/en/latest/) |
| Release docs | [stable](https://ab-sdk.readthedocs.io/en/stable/), plus the exact tag version |

## 1. Verify publishing connections

The current GitHub Actions workflow builds and tests pushed release tags matching
`v*.*.*`, checks the tag against `pyproject.toml`, builds distributions, validates
them with Twine, and uploads to PyPI using the `PYPI_API_TOKEN` repository secret.
Verify that this secret and PyPI project permissions are configured on the
**origin** source repository. PyPI publication is restricted to
`bmonson-annex/annex-abconnect`; the organization's copy runs validation but does
not upload a duplicate package. Do not assume settings followed a repository move.
Do not print secret values in release evidence.

Read the Docs builds separately through its Git integration and
`.readthedocs.yaml`; the PyPI workflow does not deploy the hosted docs.

The RTD project points at `https://github.com/AnnexBrands/annex-abconnect`.
Keep that connection and synchronize reviewed commits from `origin`
(`gh-ab:bmonson-annex/annex-abconnect`) to `upstream`
(`gh-ab:AnnexBrands/annex-abconnect`). Adding the local remote alone does not
update the hosted repository. Push `main` to both remotes and verify they contain
the same reviewed commit before publishing:

```bash
git push origin main
git push upstream main
```

Retain `main` as RTD's default branch and `stable` as its default documentation
version. The organization repository has a manually configured push webhook to
the existing ab-sdk integration. It returned HTTP 200 during 0.3.0 publication;
verify its current delivery status for each release.

Verify a webhook delivery and a successful `latest` build against the intended
commit. Confirm the relevant release versions can be activated. Repository
configuration, credentials, webhooks, and RTD version activation live in the
services; editing this repository's YAML does not configure them.

The official [Git integration guide](https://docs.readthedocs.com/platform/stable/guides/setup/git-repo-manual.html)
describes webhook setup and delivery verification. RTD's
[version guide](https://docs.readthedocs.com/platform/stable/versions.html)
explains activation, `latest`, `stable`, and the default-version setting.

## 2. Prepare and validate the release commit

1. Fetch the current source and tags and confirm the baseline. For 0.3.0, retain
   all changes through v0.2.3 and the subsequent CLI token-refresh addition.
2. Finish the 8_01 release scope, compatibility matrix, real fixture validation,
   and [DX acceptance measures](dx-roadmap.md). Resolve remaining gaps rather
   than publishing the current migration preview as completed support.
3. Set `project.version` in `pyproject.toml` to the final release version. Update
   the lockfile if needed by the project's dependency workflow. Replace the
   Unreleased changelog entry with the actual date and implemented behavior.
4. Update What's New, the home-page release status, quickstart version examples,
   final migration guide, endpoint docs, fixture status, and generated progress.
5. Run the deterministic gates from the repository root:

```bash
uv sync --group docs
uv run ruff check .
uv run pytest -m "not live"
uv run python scripts/generate_progress.py --check
uv run sphinx-build -b html -W --keep-going docs docs/_build/html
```

Run safe staging integration checks required by the changed contracts and record
their results separately. Inspect rendered home, quickstart, What's New,
migration, and key reference pages. Review and merge the release changes; the
working tree and release commit must be clean before tagging.

## 3. Publish the package to PyPI

Set these values to the approved release and run from the reviewed release
commit. Pushing the tag triggers package publication through GitHub Actions.

```bash
RELEASE_VERSION=0.3.0
RELEASE_TAG="v${RELEASE_VERSION}"
git status --short
git rev-parse HEAD
git tag -a "$RELEASE_TAG" -m "Release $RELEASE_VERSION"
git push origin "$RELEASE_TAG"
```

Watch the tag's workflow in
[GitHub Actions](https://github.com/bmonson-annex/annex-abconnect/actions).
Both validation and the PyPI publish job must succeed. The workflow's tag/version
check must pass. The configured PyPI publisher follows the
[Python Packaging publication workflow](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).

Verify the release page at
`https://pypi.org/project/annex-abconnect/<version>/` contains the wheel and source
distribution. From outside the source checkout, create a fresh virtual
environment and install the exact version from PyPI:

```bash
python -m venv /tmp/ab-release-verification
/tmp/ab-release-verification/bin/python -m pip install "annex-abconnect==$RELEASE_VERSION"
/tmp/ab-release-verification/bin/python -c "from importlib.metadata import version; import ab; print(version('annex-abconnect')); print(ab.__file__)"
/tmp/ab-release-verification/bin/ab --help
```

Use a new empty environment path for each verification. Confirm the printed
version equals the release version and `ab.__file__` points into that environment,
not a checkout. This verifies installation and CLI discovery; it does not replace
the release's API contract checks.

## 4. Publish matching documentation on Read the Docs

After verifying the PyPI release, push the same release tag to the organization
repository consumed by RTD:

```bash
git push upstream "$RELEASE_TAG"
```

1. Open the [project's versions](https://app.readthedocs.org/projects/ab-sdk/versions/).
   Sync versions (triggering a build also syncs them) if the tag is missing.
2. Activate the new stable tag's version and trigger its build if necessary.
   Confirm the [build log](https://app.readthedocs.org/projects/ab-sdk/builds/)
   checks out exactly the release commit and succeeds with warnings treated as
   errors. Verify the installed package version shown in the docs matches it.
3. Open the exact version's documentation URL from RTD's version page. Confirm
   home, What's New, quickstart, migration, and API/model reference pages load.
4. Confirm `stable` resolves to the intended stable release and has a successful
   build. `latest` remains the development branch. Set the project's default
   version to `stable` for package users and verify the root URL lands there.
5. Check the version selector exposes the release and preserves older versions
   still needed by supported users. Record the build URL, commit, version slug,
   and public docs URLs.

## 5. Close the release with evidence

Publish the GitHub release notes from the final changelog and link the PyPI
version, matching RTD version, and migration guide. Record:

- [ ] SDK version, server compatibility, Git tag, and exact release commit.
- [ ] Successful CI run and required staging validation evidence.
- [ ] PyPI release URL, wheel/sdist filenames, and fresh-install verification.
- [ ] RTD version/build URL and verified release commit.
- [ ] Public versioned docs, stable/root routing, and navigation checks.
- [ ] What's New, migration examples, compatibility warnings, and DX review results.

Keep publication incomplete if either destination is missing or out of date.

## Recover a partial publication

- **CI or upload failed:** inspect the failed job. Fix the cause and rerun only
  when the release artifact and tag still match the reviewed commit. The existing
  publisher skips existing files; verify both artifacts rather than assuming a
  rerun replaced anything. Use a new version for changed published code.
- **PyPI succeeded, RTD failed:** retain the published artifact and fix the RTD
  repository, dependency, version, or build issue. Rebuild the release's docs and
  complete the verification checklist; do not mark docs published prematurely.
- **Docs succeeded, PyPI failed:** verify the package upload and clean-install
  check before announcing the release. A docs build is not package evidence.
