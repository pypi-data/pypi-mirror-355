"""Tests for the ProjectXClient class."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from projectx_sdk import ProjectXClient
from projectx_sdk.exceptions import AuthenticationError, ProjectXError, ResourceNotFoundError


class TestProjectXClient:
    """Tests for the ProjectXClient class."""

    @pytest.fixture(autouse=True)
    def setup_temp_cache(self):
        """Set up a temporary cache directory for each test."""
        # Clear any existing global cache files first
        self._clear_global_cache()

        # Create a temporary directory for this test
        self.temp_cache_dir = Path(tempfile.mkdtemp())
        yield
        # Clean up after the test
        shutil.rmtree(self.temp_cache_dir, ignore_errors=True)
        # Clear global cache again after test
        self._clear_global_cache()

    def _clear_global_cache(self):
        """Clear global token cache directories."""
        cache_paths = [
            Path.home() / ".projectx_sdk",
            Path.cwd() / ".projectx_tokens",
            Path(tempfile.gettempdir()) / ".projectx_tokens",
        ]
        for cache_path in cache_paths:
            if cache_path.exists():
                shutil.rmtree(cache_path, ignore_errors=True)

    def _patch_client_cache(self, client):
        """Override the client's auth cache directory to use temp directory."""
        client.auth._cache_dir = self.temp_cache_dir
        client.auth._token_file = (
            client.auth._cache_dir / f"token_{client.auth._get_cache_key()}.json"
        )
        return client

    def test_init_with_environment(self):
        """Test client initialization with a valid environment."""
        client = ProjectXClient(environment="demo")
        assert client.base_url == "https://gateway-api-demo.s2f.projectx.com"

    def test_init_with_invalid_environment(self):
        """Test client initialization with an invalid environment."""
        with pytest.raises(ValueError) as excinfo:
            ProjectXClient(environment="invalid_env")
        assert "Unknown environment" in str(excinfo.value)

    def test_init_with_base_url(self):
        """Test client initialization with a custom base URL."""
        base_url = "https://custom-api.example.com"
        client = ProjectXClient(base_url=base_url)
        assert client.base_url == base_url

    def test_init_with_api_key_auth(self, mock_responses, mock_api_key_auth):
        """Test client initialization with API key authentication."""
        client = ProjectXClient(username="test_user", api_key="test_api_key", environment="demo")
        self._patch_client_cache(client)
        assert client.auth is not None
        assert client.auth.token is not None

    @patch("projectx_sdk.auth.Authenticator.authenticate_with_app")
    @patch("projectx_sdk.auth.Authenticator._load_token_from_cache")
    def test_init_with_app_auth(self, mock_load_cache, mock_auth_app, mock_responses):
        """Test client initialization with app credentials."""
        password = "test_password"
        device_id = "test_device"
        app_id = "test_app_id"
        verify_key = "test_verify_key"

        # Mock cache loading to return nothing (force authentication)
        mock_load_cache.return_value = None

        # Mock successful app authentication
        mock_auth_app.return_value = True

        # Initialize client with app auth
        client = ProjectXClient(
            username="test_user",
            password=password,
            device_id=device_id,
            app_id=app_id,
            verify_key=verify_key,
            environment="demo",
        )

        # Check that authenticate_with_app was called
        mock_auth_app.assert_called_once()

    def test_request_unauthenticated(self):
        """Test making a request when not authenticated."""
        client = ProjectXClient(environment="demo")

        # Patch the get_token method to raise an AuthenticationError
        with patch.object(client.auth, "get_token") as mock_get_token:
            mock_get_token.side_effect = AuthenticationError("No authentication token available")

            # Try to make a request
            with pytest.raises(AuthenticationError) as excinfo:
                client.request("GET", "/api/test")

            assert "No authentication token available" in str(excinfo.value)

    def test_request_authenticated(self, authenticated_client, mock_responses, api_base_url):
        """Test making a successful authenticated request."""
        # Mock a successful response
        mock_responses.add(
            mock_responses.GET,
            f"{api_base_url}/api/test",
            json={"success": True, "data": {"test": "value"}},
            status=200,
        )

        # Make the request
        response = authenticated_client.request("GET", "/api/test")

        # Check the response
        assert response["success"] is True
        assert response["data"]["test"] == "value"

    def test_request_api_error(self, authenticated_client, mock_responses, api_base_url):
        """Test handling API errors in responses."""
        # Mock an API error response (success=false)
        mock_responses.add(
            mock_responses.GET,
            f"{api_base_url}/api/test",
            json={"success": False, "errorCode": 1001, "errorMessage": "Test error"},
            status=200,
        )

        # Make the request - should raise a ProjectXError
        with pytest.raises(ProjectXError) as excinfo:
            authenticated_client.request("GET", "/api/test")

        # Check the exception
        assert "Test error" in str(excinfo.value)
        assert excinfo.value.error_code == 1001

    def test_request_http_error(self, authenticated_client, mock_responses, api_base_url):
        """Test handling HTTP errors in responses."""
        # Mock an HTTP error response
        mock_responses.add(
            mock_responses.GET,
            f"{api_base_url}/api/test",
            json={"message": "Not found"},
            status=404,
        )

        # Make the request - should raise a ResourceNotFoundError
        with pytest.raises(ResourceNotFoundError) as excinfo:
            authenticated_client.request("GET", "/api/test")

        # Check the exception
        assert "Resource not found" in str(excinfo.value)

    def test_lazy_service_loading(self, authenticated_client):
        """Test that service endpoints are available."""
        # All services should be initialized and available
        assert authenticated_client.accounts is not None
        assert authenticated_client.contracts is not None
        assert authenticated_client.history is not None
        assert authenticated_client.orders is not None
        assert authenticated_client.positions is not None
        assert authenticated_client.trades is not None

        # Real-time client should be lazy-loaded
        assert authenticated_client._realtime is None
        realtime = authenticated_client.realtime
        assert realtime is not None
        assert authenticated_client._realtime is realtime
