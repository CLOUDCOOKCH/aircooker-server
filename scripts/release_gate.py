"""Release policy: exact-source CI, explicit RC channels and evidence-backed stable tags."""

import ast
import json
import os
import re
import sys
import tomllib
from pathlib import Path

from preview_gate import select_run, verify_jobs
from preview_release import completed_digest, fetch_release

REQUIRED_GATES = {
    "scope",
    "core_workflows",
    "offline_recovery",
    "backup_restore_upgrade",
    "data_deletion",
    "resource_limits",
    "security_review",
    "physical_iphone",
    "live_ai",
    "live_bring",
    "live_reminders",
    "release_pipeline",
    "operator_documentation",
    "household_pilot",
}


def release_version(tag):
    match = re.fullmatch(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-rc\.([1-9]\d*))?", tag)
    if not match:
        raise ValueError("Use vMAJOR.MINOR.PATCH or vMAJOR.MINOR.PATCH-rc.N")
    major, minor, patch, candidate = match.groups()
    version = f"{major}.{minor}.{patch}"
    return (version + f"rc{candidate}" if candidate else version), bool(candidate)


def validate_metadata(root, tag):
    expected, candidate = release_version(tag)
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    assignments = ast.parse((root / "src/aircooker/__init__.py").read_text()).body
    versions = [
        ast.literal_eval(node.value)
        for node in assignments
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
    ]
    if project != expected or versions != [expected]:
        raise ValueError("Tag, project version and installed API version must match")
    return candidate


def validate_acceptance(document, tag):
    if document.get("schema_version") != 1 or document.get("version") != tag.removeprefix("v"):
        raise ValueError("Acceptance document must describe this exact stable version")
    gates = document.get("gates", [])
    if {row.get("id") for row in gates} != REQUIRED_GATES or len(gates) != len(REQUIRED_GATES):
        raise ValueError("Stable acceptance must cover every required gate exactly once")
    for gate in gates:
        evidence = gate.get("evidence")
        if gate.get("status") != "passed" or not isinstance(evidence, list) or not evidence:
            raise ValueError(f"Production gate is not verified: {gate.get('id')}")
        if any(not isinstance(item, str) or not item.strip() for item in evidence):
            raise ValueError("Gate evidence must contain concrete document/run references")


def main():
    stage = sys.argv[1]
    root = Path(__file__).resolve().parents[1]
    tag, sha, repository = (
        os.environ["GITHUB_REF_NAME"],
        os.environ["GITHUB_SHA"],
        os.environ["GITHUB_REPOSITORY"],
    )
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid repository")
    if stage == "metadata":
        candidate = validate_metadata(root, tag)
        if not candidate:
            validate_acceptance(
                json.loads((root / "docs/release/v1-acceptance.json").read_text()), tag
            )
        image = f"ghcr.io/{repository.split('/')[0].lower()}/mealf-server"
        release = fetch_release(repository, tag, os.environ["GH_TOKEN"])
        digest = completed_digest(release, tag, image, prerelease=candidate)
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"channel={'rc' if candidate else 'stable'}\n")
            output.write(f"environment={'release-candidate' if candidate else 'release'}\n")
            output.write(f"already_published={'true' if digest else 'false'}\n")
        if digest:
            print(f"Completed release retained unchanged: {image}@{digest}")
    elif stage == "run":
        payload = json.loads(Path(sys.argv[2]).read_text())
        run_id = select_run(payload, sha, repository)
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"run_id={run_id}\n")
    elif stage == "jobs":
        verify_jobs(json.loads(Path(sys.argv[2]).read_text()), sha)
    else:
        raise ValueError("Unknown release gate stage")


if __name__ == "__main__":
    main()
