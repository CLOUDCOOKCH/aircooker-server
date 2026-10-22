"""Pin the release's install example to the exact verified public manifest."""

import os
import re
from pathlib import Path


def compose_for_image(template, image, digest):
    if not re.fullmatch(r"ghcr\.io/[a-z0-9][a-z0-9_.-]*/mealf-server", image):
        raise ValueError("Unexpected release image")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
        raise ValueError("Missing immutable manifest digest")
    rendered, count = re.subn(
        r"\$\{MEALF_IMAGE:-ghcr\.io/[a-z0-9_.-]+/mealf-server:[^}]+\}",
        "${MEALF_IMAGE:-" + image + "@" + digest + "}",
        template,
    )
    if count != 1:
        raise ValueError("Install template must have exactly one mealf image default")
    return rendered


def main():
    root = Path(__file__).resolve().parents[1]
    rendered = compose_for_image(
        (root / "compose.preview.yaml").read_text(),
        os.environ["PUBLISHED_IMAGE"],
        os.environ["PUBLISHED_DIGEST"],
    )
    (root / "release-assets/compose.release.yaml").write_text(rendered)


if __name__ == "__main__":
    main()
