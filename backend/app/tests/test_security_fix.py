from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app import crud
from app.core.security import DUMMY_PASSWORD_HASH


def test_authenticate_user_not_found_timing_attack_mitigation(db: Session) -> None:
    """
    Test verify_password is called with DUMMY_PASSWORD_HASH when user is not found.
    """
    email = "nonexistent@example.com"
    password = "randompassword"

    # Mock verify_password to track calls
    with patch("app.crud.crud_user.verify_password") as mock_verify_password:
        # Mock get_by_email to return None (user not found)
        with patch.object(crud.user, "get_by_email", return_value=None):
            result = crud.user.authenticate(db, email=email, password=password)

            assert result is None

            # Verify that verify_password was called with the dummy hash
            mock_verify_password.assert_called_once_with(password, DUMMY_PASSWORD_HASH)


def test_authenticate_user_inactive_timing_attack_mitigation(db: Session) -> None:
    """
    Test verify_password is called with DUMMY_PASSWORD_HASH when user is inactive.
    """
    email = "inactive@example.com"
    password = "randompassword"

    # Create a mock user that is inactive
    mock_user = MagicMock()
    mock_user.is_active = False
    mock_user.email = email

    # Mock verify_password to track calls
    with patch("app.crud.crud_user.verify_password") as mock_verify_password:
        # Mock get_by_email to return our inactive user
        with patch.object(crud.user, "get_by_email", return_value=mock_user):
            result = crud.user.authenticate(db, email=email, password=password)

            assert result is None

            # Verify that verify_password was called with the dummy hash
            mock_verify_password.assert_called_once_with(password, DUMMY_PASSWORD_HASH)
