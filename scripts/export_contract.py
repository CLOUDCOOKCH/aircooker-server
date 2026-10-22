import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from mealf.app import create_app

parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
with TemporaryDirectory() as directory:
    schema = create_app(Path(directory), False).openapi()
# Explicit payload schemas are generated from the same Pydantic models as runtime validation.
content = json.dumps(schema, indent=2, sort_keys=True) + "\n"
target = Path("contracts/openapi-v1.json")
if args.check:
    if not target.exists() or target.read_text() != content:
        raise SystemExit(
            "OpenAPI contract drift; run scripts/export_contract.py and review the diff"
        )
else:
    target.parent.mkdir(exist_ok=True)
    target.write_text(content)
