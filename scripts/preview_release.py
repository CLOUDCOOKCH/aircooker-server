"""Read-only preflight: an already completed preview must never be rebuilt on retry."""

import json
import os
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def completed_digest(release, tag, image, *, prerelease=True):
    if release is None:
        return None
    if (
        release.get("tag_name") != tag
        or release.get("draft") is not False
        or release.get("prerelease") is not prerelease
    ):
        raise ValueError(
            "Existing release is not the expected completed preview; inspect it manually"
        )
    match = re.fullmatch(
        r"Image: `" + re.escape(image) + r"@(sha256:[a-f0-9]{64})`",
        release.get("body", "").split("\n", 1)[0].strip(),
    )
    if match is None:
        raise ValueError("Existing preview lacks a pinned image digest; refusing to replace it")
    return match.group(1)


def fetch_release(repository, tag, token):
    request = Request(
        f"https://api.github.com/repos/{repository}/releases/tags/{tag}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        # Authentication/network/rate-limit failures never mean a free release tag.
        raise


def main():
    repository, tag = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_REF_NAME"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not re.fullmatch(
        r"poc-[0-9]{8}\.[1-9][0-9]*", tag
    ):
        raise ValueError("Invalid repository or preview tag")
    image = f"ghcr.io/{repository.split('/')[0].lower()}/mealf-server"
    digest = completed_digest(fetch_release(repository, tag, os.environ["GH_TOKEN"]), tag, image)
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"already_published={'true' if digest else 'false'}\n")
    if digest:
        message = f"{tag} is already released at {image}@{digest}. No image or release is changed."
        print(message)
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(message + "\nUse a fresh tag to publish newer source.\n")


if __name__ == "__main__":
    main()
