"""Package the supplied mealf PNGs without redrawing or recolouring their artwork.

Original uploads remain byte-for-byte intact. Only transparent outer space, output size
and the opaque canvas required for installation icons are adjusted in web derivatives.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / "assets/brand/originals"
PUBLIC = ROOT / "frontend/public"
CANVAS = "#fff7ec"


def png(image):
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def fitted(image, size, *, opaque=False, extent=None):
    canvas = Image.new("RGBA", (size, size), CANVAS if opaque else (0, 0, 0, 0))
    fitted = ImageOps.contain(image, (extent or size, extent or size), Image.Resampling.LANCZOS)
    canvas.alpha_composite(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2))
    return canvas.convert("RGB") if opaque else canvas


def build():
    sources = {}
    originals = {}
    for role, filename in (
        ("peach", "mealf-flirty-peach-logo.png"),
        ("wordmark", "mealf-flirty-peach-wortmarke.png"),
    ):
        path = ORIGINALS / filename
        with Image.open(path) as image:
            assert image.format == "PNG" and max(image.size) <= 4096
            rgba = image.convert("RGBA")
            bounds = rgba.getchannel("A").getbbox()
            assert bounds
            originals[role] = rgba.crop(bounds)
            sources[role] = {
                "file": "assets/brand/originals/" + filename,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size": list(image.size),
                "transparent_trim": list(bounds),
            }
    peach = originals["peach"]
    wordmark = originals["wordmark"]
    wordmark = ImageOps.contain(wordmark, (512, 512), Image.Resampling.LANCZOS)
    outputs = {
        "brand/peach-v1.png": png(fitted(peach, 384)),
        "brand/wordmark-v1.png": png(wordmark),
        "brand/icon-64-v1.png": png(fitted(peach, 64, opaque=True)),
        "brand/apple-touch-icon-v1.png": png(fitted(peach, 180, opaque=True)),
        "brand/icon-192-v1.png": png(fitted(peach, 192, opaque=True)),
        "brand/icon-512-v1.png": png(fitted(peach, 512, opaque=True)),
        # A 288px square fits entirely inside the 80%-diameter safe circle at 512px.
        "brand/maskable-512-v1.png": png(fitted(peach, 512, opaque=True, extent=288)),
    }
    # Older shell/manifest URLs continue to resolve to the new artwork.
    outputs["icon-192.png"] = outputs["brand/icon-192-v1.png"]
    outputs["icon-512.png"] = outputs["brand/icon-512-v1.png"]
    manifest = {
        "version": 1,
        "origin": "Original PNG artwork supplied by the user in mealf-flirty-peach-wortmarke.zip",
        "sources": sources,
        "processing": "Trim fully transparent margins, proportionally resize and centre; preserve artwork colours and alpha. Installation icons have an opaque cream canvas; maskable artwork stays in the safe circle.",
        "icon_canvas": CANVAS,
        "outputs": {
            name: {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
            for name, content in outputs.items()
        },
    }
    outputs["brand/provenance.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in build().items():
        path = PUBLIC / name
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                raise SystemExit("Brand asset drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print(
        "Verified original mealf artwork and web/install derivatives"
        if args.check
        else "Built mealf brand assets from the original PNGs"
    )


if __name__ == "__main__":
    main()
