import os
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken

from .errors import DomainError


class SecretVault:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        key = root / "integrations.key"
        if not key.exists():
            try:
                fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as out:
                    out.write(Fernet.generate_key())
            except FileExistsError:
                pass
        self.cipher = Fernet(key.read_bytes())

    def save(self, name: str, value: str):
        target = self.root / (name + ".enc")
        temporary = self.root / (name + "." + str(uuid4()) + ".tmp")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as out:
            out.write(self.cipher.encrypt(value.encode()))
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, target)

    def load(self, name: str):
        target = self.root / (name + ".enc")
        if not target.exists():
            return None
        try:
            return self.cipher.decrypt(target.read_bytes()).decode()
        except InvalidToken as exc:
            raise DomainError("integration_secret_unavailable", 503) from exc

    def remove(self, name: str):
        (self.root / (name + ".enc")).unlink(missing_ok=True)
