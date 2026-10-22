"""Linux/macOS local data-volume lease shared by the server and offline maintenance."""

import fcntl
import os
from pathlib import Path


class InstanceLock:
    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.fd = os.open(root / ".instance.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self.fd)
            self.fd = -1
            raise RuntimeError(
                "Stop the server and other offline maintenance before proceeding"
            ) from exc

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
