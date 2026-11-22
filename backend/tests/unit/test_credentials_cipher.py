from cryptography.fernet import Fernet

from tracelens.security.credentials import CredentialCipher


def test_credential_cipher_roundtrip() -> None:
    key = Fernet.generate_key().decode()
    cipher = CredentialCipher(key)
    payload = {"api_key": "sk-test"}
    token = cipher.encrypt_json(payload)
    assert token != "sk-test"
    assert cipher.decrypt_json(token) == payload
