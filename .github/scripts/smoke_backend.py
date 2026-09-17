#!/usr/bin/env python3
"""Smoke-test the web UI's Flask API against the committed sample data.

The backend reads decomposition and agreement JSON off disk and reshapes it
for the UI. Nothing in the unit suite covers that: a renamed fixture, a moved
directory, or a changed analysis schema shows up only when a route is
actually called. This calls every route and checks the payload the frontend
depends on is present.

Run from `webui/backend/`:

    python ../../.github/scripts/smoke_backend.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# The app resolves its data directories relative to its own location, so it
# must be imported from webui/backend/.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "webui" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import app as backend_app  # noqa: E402


def main() -> int:
    client = backend_app.app.test_client()
    failures: list[str] = []

    def get(path: str, expected: int = 200):
        response = client.get(path)
        marker = "ok " if response.status_code == expected else "FAIL"
        print(f"{marker} {response.status_code}  {path}")
        if response.status_code != expected:
            failures.append(f"{path} returned {response.status_code}, expected {expected}")
            return None
        return response.get_json()

    get("/api/health")

    reviewers = get("/api/reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        failures.append("/api/reviewers returned no reviewers")

    trials = get("/api/trials")
    if not isinstance(trials, list) or not trials:
        print("FAIL /api/trials returned no trials -- is sample_data/decomposed populated?")
        failures.append("/api/trials returned no trials")
        print_summary(failures)
        return 1

    nct = trials[0]
    trial = get(f"/api/trials/{nct}")
    if isinstance(trial, dict) and not trial.get("criteria"):
        failures.append(f"trial {nct} has no criteria")

    if reviewers:
        get(f"/api/trials/{nct}/decompositions/{reviewers[0]}")

    comparison = get(f"/api/trials/{nct}/comparison")
    if isinstance(comparison, dict):
        # These four keys are exactly what webui/frontend/src/lib/api.ts
        # types as CriteriaComparison and what page.tsx destructures.
        for key in ("trial", "reviewers", "decompositions", "agreement"):
            if key not in comparison:
                failures.append(f"/comparison payload is missing {key!r}")
        print(f"ok  comparison payload keys: {sorted(comparison)}")

    print_summary(failures)
    return 1 if failures else 0


def print_summary(failures: list[str]) -> None:
    print()
    if failures:
        print(f"{len(failures)} failure(s):")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print("all routes OK")


if __name__ == "__main__":
    sys.exit(main())
