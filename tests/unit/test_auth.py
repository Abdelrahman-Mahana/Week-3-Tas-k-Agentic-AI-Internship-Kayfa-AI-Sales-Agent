"""Unit tests for core/auth.py"""

import pytest
from core.auth import hash_password, verify_password


def test_password_hashing():
    plain = "testpassword123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True


def test_password_verification_failure():
    plain = "testpassword123"
    hashed = hash_password(plain)
    assert verify_password("wrongpassword", hashed) is False


def test_password_hashing_different_salts():
    plain = "testpassword123"
    hashed1 = hash_password(plain)
    hashed2 = hash_password(plain)
    # Different hashes due to different salts
    assert hashed1 != hashed2
    # Both should verify
    assert verify_password(plain, hashed1) is True
    assert verify_password(plain, hashed2) is True
