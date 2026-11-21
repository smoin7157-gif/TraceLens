from tracelens.security.keys import hash_api_key, issue_api_key, parse_api_key, verify_api_key


def test_issue_api_key_stores_hash_not_plaintext() -> None:
    material = issue_api_key()
    assert material.raw_key.startswith("tl_")
    assert material.key_hash != material.raw_key
    assert material.key_prefix in material.raw_key
    assert verify_api_key(material.raw_key, material.key_hash)


def test_parse_api_key_format() -> None:
    material = issue_api_key()
    parsed = parse_api_key(material.raw_key)
    assert parsed is not None
    assert parsed[0] == material.key_prefix


def test_verify_rejects_wrong_secret() -> None:
    material = issue_api_key()
    assert not verify_api_key(material.raw_key + "x", material.key_hash)


def test_hash_is_deterministic_verify_only() -> None:
    raw = issue_api_key().raw_key
    h1 = hash_api_key(raw)
    h2 = hash_api_key(raw)
    assert h1 != h2
    assert verify_api_key(raw, h1)
    assert verify_api_key(raw, h2)
