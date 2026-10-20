import pytest

from aircooker.errors import DomainError
from aircooker.secrets import SecretVault


def test_integration_credentials_encrypted_and_recoverable(tmp_path):
    vault = SecretVault(tmp_path)
    value = "synthetic integration credential"
    vault.save("bring", value)
    encrypted = (tmp_path / "bring.enc").read_bytes()
    assert value.encode() not in encrypted
    assert SecretVault(tmp_path).load("bring") == value
    assert (tmp_path / "bring.enc").stat().st_mode & 0o077 == 0
    assert (tmp_path / "integrations.key").stat().st_mode & 0o077 == 0
    vault.remove("bring")
    assert vault.load("bring") is None


def test_corrupted_secret_is_an_explicit_failure(tmp_path):
    vault = SecretVault(tmp_path)
    vault.save("bring", "synthetic")
    (tmp_path / "bring.enc").write_bytes(b"not valid ciphertext")
    with pytest.raises(DomainError, match="integration_secret_unavailable"):
        vault.load("bring")
