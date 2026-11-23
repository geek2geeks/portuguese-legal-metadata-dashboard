#!/usr/bin/env python3
"""CI smoke test for the ECLI Metadata Dashboard.

Runs the Flask test client against the sample database seeded by
``scripts/init_database.py`` and fails with a non-zero exit code when an
endpoint returns an unexpected status or the seeded data is missing.
"""

import os
import sys

# Make the repository root importable when this file is run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard import app  # noqa: E402

EXPECTED_DOCUMENTS = 50
GET_PATHS = (
    "/",
    "/api/stats",
    "/api/courts",
    "/api/years",
    "/api/metrics",
    "/api/recent",
    "/api/search?court=STJ",
    "/api/search?year=2024",
)


def main():
    """Run the HTTP smoke checks and return a process exit code."""
    failures = []
    client = app.test_client()

    for path in GET_PATHS:
        response = client.get(path)
        print(f"GET {path} -> {response.status_code}")
        if response.status_code != 200:
            failures.append(f"GET {path} returned {response.status_code}")

    stats = client.get("/api/stats").get_json()
    print(f"total_documents: {stats.get('total_documents')}")
    if stats.get("total_documents") != EXPECTED_DOCUMENTS:
        failures.append(
            f"expected {EXPECTED_DOCUMENTS} seeded documents, "
            f"got {stats.get('total_documents')}"
        )

    recent = client.get("/api/recent").get_json()
    if not isinstance(recent, list) or not recent:
        failures.append("/api/recent did not return documents")
    else:
        ecli_id = str(recent[0]["ecli_id"])
        response = client.get(f"/api/document/{ecli_id}")
        print(f"GET /api/document/{ecli_id} -> {response.status_code}")
        if response.status_code != 200:
            failures.append(f"GET /api/document returned {response.status_code}")

    response = client.post(
        "/api/feedback",
        json={
            "type": "rating",
            "rating": 5,
            "comment": "ci smoke",
            "document_id": "ci",
            "user_agent": "ci",
        },
    )
    print(f"POST /api/feedback -> {response.status_code}")
    if response.status_code != 200:
        failures.append(f"POST /api/feedback returned {response.status_code}")

    if failures:
        print("SMOKE TEST FAILURES:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
