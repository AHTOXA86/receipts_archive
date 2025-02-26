from app.routes.user import login_for_access_token
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.models import UserCreate, User
from app.routes.user import create_user
from sqlmodel import Session
from unittest.mock import MagicMock, patch
import pytest


class TestUser:
    def test_create_user_successful(self):
        """
        Test successful user creation when email is not already registered.

        This test verifies that:
        1. The create_user function creates a new user when given valid input
        2. The created user has the correct attributes
        3. The session's add and commit methods are called
        4. The session's refresh method is called on the new user
        5. The function returns the newly created user
        """
        # Mock UserCreate object
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
        )

        # Mock Session object
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        # Call the function under test
        result = create_user(user_create, mock_session)

        # Assertions
        assert isinstance(result, User)
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.full_name == "Test User"
        assert result.hashed_password != "password123"  # Password should be hashed

        # Verify session methods were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(result)

    async def test_login_for_access_token_successful(self):
        """
        Test successful login with valid credentials.

        This test verifies that:
        1. The login_for_access_token function returns a token when given valid credentials
        2. The returned token has the expected structure
        3. The authenticate_user function is called with the correct parameters
        4. The create_access_token function is called with the correct parameters
        """
        # Mock form data with valid credentials
        mock_form_data = OAuth2PasswordRequestForm(
            username="valid_user", password="valid_password"
        )
        mock_session = MagicMock(spec=Session)

        # Mock the authenticated user
        mock_user = MagicMock()
        mock_user.username = "valid_user"

        # Mock the token
        mock_token = "mock_access_token"

        # Patch both authenticate_user and create_access_token
        with patch(
            "app.routes.user.authenticate_user", return_value=mock_user
        ) as mock_authenticate:
            with patch(
                "app.routes.user.create_access_token", return_value=mock_token
            ) as mock_create_token:
                # Call the function under test
                result = await login_for_access_token(
                    form_data=mock_form_data, session=mock_session
                )

                # Verify authenticate_user was called with correct parameters
                mock_authenticate.assert_called_once_with(
                    mock_session, mock_form_data.username, mock_form_data.password
                )

                # Verify create_access_token was called with correct parameters
                mock_create_token.assert_called_once()
                args, kwargs = mock_create_token.call_args
                assert "sub" in kwargs["data"]
                assert kwargs["data"]["sub"] == "valid_user"

                # Verify the result structure
                assert "access_token" in result
                assert result["access_token"] == mock_token
                assert result["token_type"] == "bearer"

    async def test_login_for_access_token_invalid_credentials(self):
        """
        Test the login_for_access_token function with invalid credentials.
        This test verifies that the function raises an HTTPException with status code 401
        when provided with incorrect username or password.
        """
        # Mock the necessary dependencies
        form_data = OAuth2PasswordRequestForm(
            username="test_user", password="wrong_password"
        )
        session = MagicMock(spec=Session)

        # Mock the authenticate_user function to return None (indicating invalid credentials)
        with patch("app.routes.user.authenticate_user", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await login_for_access_token(form_data=form_data, session=session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Incorrect username or password"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

            