"""Fail closed unless the exact preview commit passed the complete main-branch CI matrix."""

import json
import os
import re
import sys
from pathlib import Path

EXPECTED_JOBS = {
    "pwa-core",
    "browser",
    "checks (ubuntu-24.04)",
    "checks (ubuntu-24.04-arm)",
    "security (ubuntu-24.04)",
    "security (ubuntu-24.04-arm)",
}


def select_run(payload, sha, repository):
    matches = [
        run
        for run in payload["workflow_runs"]
        if run.get("head_sha") == sha
        and run.get("head_branch") == "main"
        and run.get("head_repository", {}).get("full_name") == repository
        and run.get("path") == ".github/workflows/ci.yml"
        and run.get("event") in {"push", "workflow_dispatch"}
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    if not matches:
        raise ValueError("No successful complete main-branch CI run for this exact commit")
    return max(matches, key=lambda run: run["id"])["id"]


def verify_jobs(pages, sha):
    jobs = [job for page in pages for job in page["jobs"]]
    actual = {job["name"] for job in jobs}
    if actual != EXPECTED_JOBS or len(jobs) != len(EXPECTED_JOBS):
        raise ValueError("CI matrix is missing jobs or has changed; review the preview gate")
    if any(
        job.get("head_sha") != sha
        or job.get("status") != "completed"
        or job.get("conclusion") != "success"
        for job in jobs
    ):
        raise ValueError("Every CI job must pass for the exact preview commit")


def main():
    stage, filename = sys.argv[1:]
    sha = os.environ["GITHUB_SHA"]
    if not re.fullmatch(r"poc-[0-9]{8}\.[1-9][0-9]*", os.environ["GITHUB_REF_NAME"]):
        raise ValueError("Preview tag must be poc-YYYYMMDD.N")
    payload = json.loads(Path(filename).read_text())
    if stage == "run":
        run_id = select_run(payload, sha, os.environ["GITHUB_REPOSITORY"])
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"run_id={run_id}\n")
        print(f"Exact source CI run: {run_id}")
    elif stage == "jobs":
        verify_jobs(payload, sha)
        print("All six exact-source CI jobs passed")
    else:
        raise ValueError("Unknown verification stage")


if __name__ == "__main__":
    main()
