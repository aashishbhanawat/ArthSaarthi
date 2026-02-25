import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.crud.crud_user import user as crud_user
from app.models.user import User
from app.core.security import DUMMY_PASSWORD_HASH

class TestAuthSecurity(unittest.TestCase):
    def test_authenticate_timing_attack_prevention(self):
        # Mock database session
        db = MagicMock(spec=Session)

        # Mock verify_password to track calls
        with patch("app.crud.crud_user.verify_password") as mock_verify_password:
            # Case 1: User does not exist
            # Mock get_by_email to return None
            with patch.object(crud_user, "get_by_email", return_value=None):
                result = crud_user.authenticate(db, email="nonexistent@example.com", password="password")

                # Should return None
                self.assertIsNone(result)

                # verify_password should be called with DUMMY_PASSWORD_HASH
                # This confirms we are preventing timing attacks by doing work even when user is not found
                mock_verify_password.assert_called_once_with("password", DUMMY_PASSWORD_HASH)

            mock_verify_password.reset_mock()

            # Case 2: User exists, wrong password
            user = MagicMock(spec=User)
            user.hashed_password = "real_hash"
            user.is_active = True

            # Mock verify_password to return False (wrong password)
            mock_verify_password.return_value = False

            with patch.object(crud_user, "get_by_email", return_value=user):
                result = crud_user.authenticate(db, email="exists@example.com", password="wrong_password")

                # Should return None
                self.assertIsNone(result)

                # verify_password should be called with user.hashed_password
                mock_verify_password.assert_called_once_with("wrong_password", "real_hash")

            mock_verify_password.reset_mock()

            # Case 3: User exists, correct password, inactive
            user.is_active = False
            mock_verify_password.return_value = True

            with patch.object(crud_user, "get_by_email", return_value=user):
                result = crud_user.authenticate(db, email="exists@example.com", password="correct_password")

                # Should return None because user is inactive
                self.assertIsNone(result)

                # verify_password should still be called
                mock_verify_password.assert_called_once_with("correct_password", "real_hash")
