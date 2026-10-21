import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "preview_gate", Path(__file__).parents[1] / "scripts/preview_gate.py"
)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
SHA = "a" * 40
REPO = "CLOUDCOOKCH/aircooker-server"


def successful_run():
    return {
        "id": 123,
        "head_sha": SHA,
        "head_branch": "main",
        "head_repository": {"full_name": REPO},
        "path": ".github/workflows/ci.yml",
        "event": "push",
        "status": "completed",
        "conclusion": "success",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("head_sha", "b" * 40),
        ("head_branch", "other"),
        ("head_repository", {"full_name": "someone/else"}),
        ("path", ".github/workflows/unrelated.yml"),
        ("event", "pull_request"),
        ("status", "in_progress"),
        ("conclusion", "failure"),
        ("conclusion", "skipped"),
    ],
)
def test_preview_rejects_unrelated_or_unsuccessful_ci(field, value):
    run = {**successful_run(), field: value}
    with pytest.raises(ValueError):
        gate.select_run({"workflow_runs": [run]}, SHA, REPO)


def test_preview_requires_each_exact_source_job_to_pass():
    assert gate.select_run({"workflow_runs": [successful_run()]}, SHA, REPO) == 123
    jobs = [
        {"name": name, "head_sha": SHA, "status": "completed", "conclusion": "success"}
        for name in sorted(gate.EXPECTED_JOBS)
    ]
    gate.verify_jobs([{"jobs": jobs[:3]}, {"jobs": jobs[3:]}], SHA)
    invalid = [jobs[:-1], jobs + [jobs[0]]]
    for field, value in [
        ("conclusion", "skipped"),
        ("conclusion", "failure"),
        ("status", "in_progress"),
        ("head_sha", "b" * 40),
    ]:
        changed = deepcopy(jobs)
        changed[0][field] = value
        invalid.append(changed)
    for changed in invalid:
        with pytest.raises(ValueError):
            gate.verify_jobs([{"jobs": changed}], SHA)


def test_manual_main_run_requires_the_same_source_and_full_matrix():
    run = {**successful_run(), "event": "workflow_dispatch"}
    assert gate.select_run({"workflow_runs": [run]}, SHA, REPO) == 123
    with pytest.raises(ValueError):
        gate.select_run({"workflow_runs": [{**run, "head_branch": "other"}]}, SHA, REPO)
