"""Gate regression ratchet test.

Loads the gate baseline (tests/gate_baseline.json) and compares current
gate evaluation results. Any gate that was previously passing but now
fails is a regression and causes the test to fail.

New passes (gates not in baseline) are allowed — run
``python scripts/update_gate_baseline.py`` to capture them.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

BASELINE_FILE = Path(__file__).parent / "gate_baseline.json"


def _evaluate_current() -> dict[str, list[str]]:
    """Evaluate all gates and return {key: [passing_gates]}."""
    from ab.progress.fixtures_generator import parse_existing_fixtures
    from ab.progress.gates import evaluate_all_gates
    from ab.progress.route_index import normalize_path

    fixtures_data = parse_existing_fixtures()

    prev_level = logging.root.level
    logging.root.setLevel(logging.ERROR)
    try:
        results = evaluate_all_gates(fixtures_data)
    finally:
        logging.root.setLevel(prev_level)

    current: dict[str, list[str]] = {}
    for status in results:
        key = f"{normalize_path(status.endpoint_path)} {status.method}"
        passing: list[str] = []
        for gate_attr, gate_id in [
            ("g1_model_fidelity", "G1"),
            ("g2_fixture_status", "G2"),
            ("g3_test_quality", "G3"),
            ("g4_doc_accuracy", "G4"),
            ("g5_param_routing", "G5"),
            ("g6_request_quality", "G6"),
        ]:
            gate_result = getattr(status, gate_attr)
            if gate_result and gate_result.passed:
                passing.append(gate_id)
        current[key] = passing
    return current


class TestGateRegression:
    def test_no_regressions(self):
        """No previously-passing gate may regress to failing."""
        if not BASELINE_FILE.exists():
            # First run — generate baseline automatically
            current = _evaluate_current()
            BASELINE_FILE.write_text(json.dumps(dict(sorted(current.items())), indent=2) + "\n")
            pytest.skip("Baseline auto-generated on first run — re-run to verify")

        baseline = json.loads(BASELINE_FILE.read_text())
        current = _evaluate_current()

        from ab.cli.discovery import discover_endpoints_from_class
        from ab.progress.route_index import normalize_path
        unsupported = {
            f"{normalize_path(m.route.path)} {m.route.method}"
            for info in discover_endpoints_from_class().values() for m in info.methods
            if m.route is not None and m.route.unsupported_reason
        }
        # 8_01 moved the document ID from the path into a required query DTO.
        # Do not keep a phantom FIXTURES row to make the retired binary route pass.
        # The new typed route is measured separately; its query/required context
        # behavior is covered by test_shipment_document_requires_franchisee_and_uses_query.
        from ab.api.endpoints.shipments import _GET_SHIPMENT_DOCUMENT

        assert _GET_SHIPMENT_DOCUMENT.path == "/shipment/document"
        assert _GET_SHIPMENT_DOCUMENT.params_model == "CurrentShipmentDocumentParams"
        assert _GET_SHIPMENT_DOCUMENT.response_model == "CarrierShippingDocument"
        unsupported.add("/shipment/document/{_} GET")
        regressions: list[str] = []
        for key, expected_gates in baseline.items():
            if key in unsupported:
                continue  # Covered by pre-transport UnsupportedOperationError regression tests.
            actual_gates = set(current.get(key, []))
            for gate in expected_gates:
                if gate not in actual_gates:
                    regressions.append(f"{key}: {gate} regressed (was PASS, now FAIL)")

        if regressions:
            msg = f"{len(regressions)} gate regression(s) detected:\n"
            msg += "\n".join(f"  - {r}" for r in sorted(regressions))
            msg += "\n\nFix the regression or update baseline with: python scripts/update_gate_baseline.py"
            pytest.fail(msg)
