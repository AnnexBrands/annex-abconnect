"""The notebook must stay a thin UI over ``ab.progress.certify`` (issue #71).

The whole point of the workbench package is that notebook steps and pytest drive
the same code. That guarantee decays the moment someone pastes real logic into a
cell, because notebook cells are not covered by the suite. These tests keep the
notebook honest without executing it (executing would require staging
credentials and would make the suite non-deterministic).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = REPO_ROOT / "notebooks" / "certify_endpoint.ipynb"


@pytest.fixture(scope="module")
def notebook() -> dict:
    if not NOTEBOOK.is_file():
        pytest.skip("certification notebook not present")
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def _code_cells(nb: dict) -> list[str]:
    return [
        "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"
    ]


def test_notebook_is_valid_and_has_content(notebook: dict) -> None:
    assert notebook["nbformat"] == 4
    assert len(_code_cells(notebook)) > 10


def test_notebook_ships_without_stored_outputs(notebook: dict) -> None:
    """Stored outputs would commit live API responses into a public repo."""
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell.get("outputs") == [], (
                "notebook contains stored outputs — clear them before committing; "
                "they may embed unsanitized live responses"
            )
            assert cell.get("execution_count") is None


def test_every_code_cell_parses(notebook: dict) -> None:
    for i, src in enumerate(_code_cells(notebook)):
        try:
            ast.parse(src)
        except SyntaxError as exc:  # pragma: no cover - failure path
            pytest.fail(f"code cell {i} has a syntax error: {exc}")


def test_notebook_defines_no_logic_of_its_own(notebook: dict) -> None:
    """No function or class definitions — logic belongs in the package."""
    for i, src in enumerate(_code_cells(notebook)):
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                pytest.fail(
                    f"code cell {i} defines {node.name!r}. The notebook is a UI — "
                    "move this into ab.progress.certify so pytest covers it."
                )


def test_notebook_uses_the_workbench_package(notebook: dict) -> None:
    joined = "\n".join(_code_cells(notebook))
    assert "from ab.progress.certify import" in joined
    assert "CertificationSession" in joined


def test_notebook_only_calls_public_workbench_api(notebook: dict) -> None:
    """Every `ab.progress.certify` name the notebook imports must be exported."""
    import ab.progress.certify as certify

    exported = set(certify.__all__)
    for src in _code_cells(notebook):
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.ImportFrom) and node.module == "ab.progress.certify":
                for alias in node.names:
                    assert alias.name in exported, (
                        f"notebook imports {alias.name!r}, which is not in "
                        "ab.progress.certify.__all__"
                    )


def test_notebook_does_not_auto_write_fixtures_or_evidence(notebook: dict) -> None:
    """Destructive steps must be commented out, not armed by default.

    Running the notebook top to bottom must not silently overwrite a committed
    fixture or evidence file.
    """
    destructive = {"approve_fixture", "write_evidence", "regenerate_report"}

    for i, src in enumerate(_code_cells(notebook)):
        tree = ast.parse(src)
        # Calls inside try/except are demonstrating a refusal (the workbench
        # raises before touching disk), so they are allowed to stay live.
        guarded = {
            id(n)
            for t in ast.walk(tree)
            if isinstance(t, ast.Try)
            for n in ast.walk(t)
            if isinstance(n, ast.Call)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or id(node) in guarded:
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            assert name not in destructive, (
                f"code cell {i} calls {name}() unguarded — it must stay commented "
                "out so a top-to-bottom run cannot overwrite committed state"
            )


def test_notebook_matches_its_generator(tmp_path, monkeypatch) -> None:
    """``scripts/generate_certify_notebook.py`` must reproduce the committed file.

    The notebook is generated, not hand-edited. Without this, a fix applied to
    one (including a ``ruff --fix`` on the notebook) silently diverges from the
    other and the next regeneration reverts it.
    """
    import subprocess
    import sys

    generator = REPO_ROOT / "scripts" / "generate_certify_notebook.py"
    if not generator.is_file():
        pytest.skip("notebook generator not present")

    before = NOTEBOOK.read_text(encoding="utf-8")
    backup = tmp_path / "backup.ipynb"
    backup.write_text(before, encoding="utf-8")
    try:
        subprocess.run(
            [sys.executable, str(generator)], cwd=str(REPO_ROOT), check=True,
            capture_output=True,
        )
        after = NOTEBOOK.read_text(encoding="utf-8")
    finally:
        NOTEBOOK.write_text(before, encoding="utf-8")

    assert after == before, (
        "notebooks/certify_endpoint.ipynb differs from what "
        "scripts/generate_certify_notebook.py produces — edit the generator, "
        "then regenerate"
    )


def test_notebook_documents_the_mutation_guard(notebook: dict) -> None:
    joined = "\n".join(
        "".join(c["source"]) for c in notebook["cells"]
    )
    assert "classify" in joined
    assert "record_restoration" in joined
    assert "unsafe_for_automation" in joined
