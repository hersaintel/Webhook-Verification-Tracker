import pytest
from hmac_service import generate_hmac, verify_hmac

KEY = b"test-secret"
MSG = b"hello world"

def test_valid_hmac_roundtrip():
    tag = generate_hmac(KEY, MSG)
    assert verify_hmac(KEY, MSG, tag) is True

def test_wrong_key_fails():
    tag = generate_hmac(KEY, MSG)
    assert verify_hmac(b"wrong-key", MSG, tag) is False

def test_tampered_message_fails():
    tag = generate_hmac(KEY, MSG)
    assert verify_hmac(KEY, b"hello world!", tag) is False

def test_different_algorithms():
    tag_sha256 = generate_hmac(KEY, MSG, "sha256")
    tag_sha512 = generate_hmac(KEY, MSG, "sha512")
    assert tag_sha256 != tag_sha512
    assert verify_hmac(KEY, MSG, tag_sha256, "sha256")
    assert not verify_hmac(KEY, MSG, tag_sha256, "sha512")

def test_empty_message():
    tag = generate_hmac(KEY, b"")
    assert verify_hmac(KEY, b"", tag)

def test_string_key_and_message():
    """Cover the str → bytes conversion paths"""
    tag = generate_hmac("test-secret", "hello world")
    assert verify_hmac("test-secret", "hello world", tag) is True

def test_mixed_types():
    """One argument str, one bytes"""
    tag = generate_hmac("test-secret", b"hello world")
    assert verify_hmac(b"test-secret", "hello world", tag) is True

def test_string_key_and_message():
    """Cover the str → bytes conversion paths"""
    tag = generate_hmac("test-secret", "hello world")
    assert verify_hmac("test-secret", "hello world", tag) is True

def test_mixed_types():
    """One argument str, one bytes"""
    tag = generate_hmac("test-secret", b"hello world")
    assert verify_hmac(b"test-secret", "hello world", tag) is True

def test_empty_key():
    """Empty key is allowed by the HMAC construction"""
    tag = generate_hmac(b"", b"message")
    assert verify_hmac(b"", b"message", tag) is True
    assert verify_hmac(b"something", b"message", tag) is False

def test_empty_key_and_message():
    tag = generate_hmac(b"", b"")
    assert verify_hmac(b"", b"", tag) is True

def test_invalid_algorithm():
    """Should raise AttributeError (or TypeError) for unknown algorithm"""
    with pytest.raises((AttributeError, ValueError)):
        generate_hmac(b"key", b"msg", algorithm="sha999")

def test_verify_with_wrong_length_hmac():
    """Completely wrong length tag must fail"""
    tag = generate_hmac(b"key", b"msg")
    assert verify_hmac(b"key", b"msg", "abc") is False          # too short
    assert verify_hmac(b"key", b"msg", tag + "00") is False     # too long

def test_case_sensitivity_of_hex():
    """HMAC hex digest is lowercase by default; uppercase should fail"""
    tag = generate_hmac(b"key", b"msg")
    upper = tag.upper()
    assert verify_hmac(b"key", b"msg", upper) is False

def test_binary_message():
    """Works with arbitrary binary data"""
    msg = bytes(range(256))          # all possible byte values
    tag = generate_hmac(b"secret", msg)
    assert verify_hmac(b"secret", msg, tag) is True