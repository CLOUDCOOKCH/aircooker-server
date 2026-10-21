import json
from datetime import datetime
from uuid import uuid4

import pytest

from aircooker.jobs import enqueue


@pytest.mark.parametrize("path", ["/api/v1/admin/jobs", "/api/v1/admin/diagnostics"])
def test_diagnostics_require_authentication(harness, path):
    client, *_ = harness
    assert client.get(path, headers={"Authorization": ""}).status_code == 401


def test_diagnostics_counts_filtering_and_redaction(harness):
    client, app, *_ = harness
    secret = "private_provider_response_with_token"
    imports = []
    with app.state.database.transaction() as db:
        for index, state in enumerate(["queued", "running", "done", "failed", "failed"]):
            enqueue(
                db, "recipe.import", str(index), {"text": secret, "url": "https://private.test"}
            )
            db.execute(
                "UPDATE background_job SET state=?,attempts=?,error_code=?,created_at=? WHERE dedupe_key=?",
                (state, index, "ai_rate_limited" if index == 4 else secret, index, str(index)),
            )
        # Future/invalid kinds must not turn into arbitrary administrator-facing text.
        enqueue(db, secret, "unknown", {"password": secret})
        for index in range(3):
            iid = str(uuid4())
            imports.append(iid)
            db.execute(
                "INSERT INTO import_draft(id,source_url,source_platform,state,recipe,warnings,error_code,confirmed_recipe_id,created_at) VALUES (?,?,?,'needs_input',?,?,?,NULL,?)",
                (
                    iid,
                    "https://private.test",
                    secret,
                    json.dumps({"title": secret}),
                    "[]",
                    secret,
                    index,
                ),
            )
    response = client.get("/api/v1/admin/diagnostics?limit=2")
    assert response.status_code == 200
    report = response.json()
    assert datetime.fromisoformat(report["captured_at"].replace("Z", "+00:00")).tzinfo
    assert report["job_counts"] == {"queued": 2, "running": 1, "done": 1, "failed": 2}
    assert len(report["recent_jobs"]) == len(report["recent_imports"]) == 2
    assert [i["id"] for i in report["recent_imports"]] == list(reversed(imports[1:]))
    assert all(i["error_code"] == "operation_failed" for i in report["recent_imports"])
    assert secret not in response.text
    assert "private.test" not in response.text
    jobs = client.get("/api/v1/admin/jobs?state=failed&limit=1").json()
    assert len(jobs) == 1 and jobs[0]["state"] == "failed"
    assert jobs[0]["error_code"] == "ai_rate_limited"
    all_jobs = client.get("/api/v1/admin/jobs")
    assert secret not in all_jobs.text
    assert "private.test" not in all_jobs.text
    assert all_jobs.json()[0]["kind"] == "unknown"
    # Diagnostics are a read projection; stored retry/payload state is unchanged.
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM background_job").fetchone()[0] == 6
        assert db.execute("SELECT error_code FROM import_draft LIMIT 1").fetchone()[0] == secret


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "limit=abc"])
def test_diagnostics_reject_unbounded_queries(harness, query):
    client, *_ = harness
    for path in ("/api/v1/admin/diagnostics", "/api/v1/admin/jobs"):
        assert client.get(path + "?" + query).status_code == 422
    assert client.get("/api/v1/admin/jobs?state=arbitrary").status_code == 422


def test_empty_diagnostics_are_typed_and_do_not_create_jobs(harness):
    client, *_ = harness
    report = client.get("/api/v1/admin/diagnostics").json()
    assert report["job_counts"] == {"queued": 0, "running": 0, "done": 0, "failed": 0}
    assert report["recent_jobs"] == report["recent_imports"] == []
    assert client.get("/api/v1/admin/jobs").json() == []
    schema = client.get("/api/v1/openapi.json").json()
    assert "AdministrationDiagnostics" in schema["components"]["schemas"]
    assert schema["paths"]["/api/v1/admin/jobs"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["items"]["$ref"].endswith("/JobInfo")
