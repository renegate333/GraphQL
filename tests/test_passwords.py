"""Тесты хэширования и политики паролей."""

import pytest

from app.core.passwords import (
    WeakPasswordError,
    hash_password,
    validate_policy,
    verify_password,
)


def test_hash_and_verify_ok():
    h = hash_password("correct horse battery staple 42")
    assert h.startswith("$argon2id$")
    assert verify_password("correct horse battery staple 42", h) is True


def test_verify_bad_password():
    h = hash_password("correct horse battery staple 42")
    assert verify_password("wrong-password", h) is False


def test_short_password_rejected():
    with pytest.raises(WeakPasswordError):
        validate_policy("short", user_inputs=[])


def test_weak_password_rejected():
    with pytest.raises(WeakPasswordError):
        validate_policy("qwerty12345678", user_inputs=[])


def test_good_password_accepted():
    # не должно бросать
    validate_policy("correct horse battery staple 42", user_inputs=["user@example.com"])