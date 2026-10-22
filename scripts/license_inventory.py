"""Inventory installed locked runtime wheels and gate licence/attribution drift.

Does not assess OS packages, bundled native libraries or third-party service terms.
"""

import argparse
import hashlib
import importlib.metadata
import importlib.resources
import json
import re
from pathlib import Path


def supplemental_notice(name: str, version: str, expression: str):
    manifest = json.loads(Path("licenses/supplemental-attribution.json").read_text())
    entry = manifest.get(name)
    if entry is None:
        return []
    if entry["version"] != version or entry["license_expression"] != expression:
        raise SystemExit("Supplemental attribution version/licence mismatch: " + name)
    content = importlib.resources.files("mealf").joinpath(entry["resource"]).read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != entry["sha256"] or not content:
        raise SystemExit("Supplemental attribution checksum mismatch: " + name)
    return [{"path": "mealf:" + entry["resource"], "sha256": digest}]


def inventory(lock: Path) -> dict:
    locked = re.findall(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)", lock.read_text(), re.MULTILINE)
    if not locked:
        raise SystemExit("No locked runtime packages found")
    components = []
    for name, version in locked:
        distribution = importlib.metadata.distribution(name)
        if distribution.version != version:
            raise SystemExit(f"Installed runtime version differs from lock: {name}")
        metadata = distribution.metadata
        expression = metadata.get("License-Expression") or metadata.get("License", "").strip()
        if expression == "Apache 2.0":
            expression = "Apache-2.0"
        if not expression or len(expression) > 200:
            raise SystemExit(f"Review missing/ambiguous licence metadata: {name}")
        notices = []
        for file in distribution.files or []:
            path = str(file)
            if ".dist-info/" not in path:
                continue
            relative = path.split(".dist-info/", 1)[1]
            if not any(
                part.lower().startswith(("license", "copying", "notice"))
                for part in Path(relative).parts
            ):
                continue
            content = Path(distribution.locate_file(file)).read_bytes()
            if not content:
                raise SystemExit(f"Empty attribution file: {name}/{relative}")
            notices.append({"path": relative, "sha256": hashlib.sha256(content).hexdigest()})
        if not notices:
            notices = supplemental_notice(name, version, expression)
        if not notices:
            raise SystemExit(f"Runtime wheel has no installed attribution files: {name}")
        components.append(
            {
                "name": name,
                "version": version,
                "license_expression": expression,
                "notices": sorted(notices, key=lambda item: item["path"]),
            }
        )
    return {
        "format": "mealf-runtime-wheel-licenses",
        "version": 1,
        "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "scope": "Installed Python runtime wheels and explicitly pinned app-shipped supplemental notices; not OS or native-library clearance",
        "components": components,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write-approval", action="store_true")
    parser.add_argument("--approval", type=Path, default=Path("licenses/runtime-approval.json"))
    parser.add_argument("--output", type=Path, default=Path("build/runtime-licenses.json"))
    args = parser.parse_args()
    if args.check and args.write_approval:
        parser.error("Approval generation and checking must be separate reviewed operations")
    report = inventory(Path("requirements.lock"))
    expected = {
        component["name"]: {
            "version": component["version"],
            "license_expression": component["license_expression"],
        }
        for component in report["components"]
    }
    if args.check and json.loads(args.approval.read_text()) != expected:
        raise SystemExit("Runtime version/licence drift: review the lock and approval manifest")
    if args.write_approval:
        args.approval.parent.mkdir(parents=True, exist_ok=True)
        args.approval.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"Inventoried {len(expected)} locked runtime wheels with verified installed or pinned app-shipped attribution"
    )


if __name__ == "__main__":
    main()
