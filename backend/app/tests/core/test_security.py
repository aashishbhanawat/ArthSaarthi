from app.core.security import get_password_hash, verify_password


def test_password_hashing():
    password = "plain_password"
    hashed_password = get_password_hash(password)
    assert hashed_password != password


def test_password_verification():
    password = "another_plain_password"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password)
    assert not verify_password("wrong_password", hashed_password)
