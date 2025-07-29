"""Authentication functionality for the ProjectX Gateway API."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from projectx_sdk.exceptions import AuthenticationError
from projectx_sdk.utils.constants import ENDPOINTS

logger = logging.getLogger(__name__)


class Authenticator:
    """
    Handles authentication and token management for the ProjectX Gateway API.

    Responsible for:
    - Initial authentication with API keys or app credentials
    - Token storage and renewal with persistent disk caching
    - Providing valid tokens for API requests
    - Preventing rate limiting through intelligent token reuse
    """

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        api_key: Optional[str] = None,
        password: Optional[str] = None,
        device_id: Optional[str] = None,
        app_id: Optional[str] = None,
        verify_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the authenticator.

        Args:
            base_url (str): The base URL for the API environment
            username (str, optional): Username for authentication
            api_key (str, optional): API key for authentication
            password (str, optional): Password for app authentication
            device_id (str, optional): Device ID for app authentication
            app_id (str, optional): App ID for app authentication
            verify_key (str, optional): Verification key for app authentication
            token (str, optional): Existing token to use
            timeout (int, optional): Request timeout in seconds
        """
        self.base_url = base_url
        self.username = username
        self.timeout = timeout

        # Store credentials for cache key generation
        self._api_key = api_key
        self._password = password
        self._device_id = device_id
        self._app_id = app_id
        self._verify_key = verify_key

        # Token management
        self.token = token
        self.token_expiry = None if token is None else datetime.now() + timedelta(hours=24)

        # Default token expiry is 24 hours from issue
        self.token_lifetime = timedelta(hours=24)

        # Set up cache directory and file paths
        self._setup_cache_paths()

        # Try to load token from cache first if no token provided
        if not self.token and username:
            self._load_token_from_cache()

        # Authenticate if credentials are provided and no token exists
        if not self.token:
            if username and api_key:
                self.authenticate_with_key(username, api_key)
            elif username and password and device_id and app_id and verify_key:
                self.authenticate_with_app(username, password, device_id, app_id, verify_key)

    def _setup_cache_paths(self):
        """Set up cache directory and file paths with fallback options."""
        # Try cache directories in order of preference
        cache_dirs = [
            Path.home() / ".projectx_sdk",  # Primary: ~/.projectx_sdk/
            Path.cwd() / ".projectx_tokens",  # Fallback: ./.projectx_tokens/
            Path.home() / ".cache" / "projectx_sdk",  # Alternative home cache
        ]

        # Add system temp as last resort
        try:
            import tempfile

            cache_dirs.append(Path(tempfile.gettempdir()) / ".projectx_tokens")
        except Exception:
            pass

        self._cache_dir = None
        self._token_file = None

        for cache_dir in cache_dirs:
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
                # Test write permissions
                test_file = cache_dir / ".test_write"
                test_file.write_text("test")
                test_file.unlink()

                self._cache_dir = cache_dir
                self._token_file = cache_dir / f"token_{self._get_cache_key()}.json"
                logger.info(f"Using cache directory: {cache_dir}")
                break
            except Exception as e:
                logger.debug(f"Cannot use cache directory {cache_dir}: {e}")
                continue

        if not self._cache_dir:
            logger.warning("No writable cache directory found - token caching disabled")

    def _get_cache_key(self) -> str:
        """Generate a unique cache key based on user credentials and environment."""
        if not self.username:
            return "anonymous"

        # Create hash from username, base_url and credentials
        key_data = f"{self.username}:{self.base_url}"
        if self._api_key:
            key_data += f":{self._api_key[:8]}"  # First 8 chars of API key
        elif self._password:
            key_data += f":{self._password[:8]}"  # First 8 chars of password

        return hashlib.md5(key_data.encode()).hexdigest()[:12]

    def _load_token_from_cache(self) -> bool:
        """
        Load a valid token from cache if available.

        Returns:
            bool: True if a valid token was loaded from cache
        """
        if not self._token_file or not self._token_file.exists():
            logger.debug("No token cache file found")
            return False

        try:
            with open(self._token_file, "r") as f:
                cache_data = json.load(f)

            # Validate cache data structure
            if not isinstance(cache_data, dict) or "token" not in cache_data:
                logger.debug("Invalid cache data structure")
                return False

            # Check if token is expired
            expiry_str = cache_data.get("expiry")
            if not expiry_str:
                logger.debug("No expiry date in cache")
                return False

            expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
            if expiry <= datetime.now():
                logger.debug("Cached token is expired")
                return False

            # Load token data
            self.token = cache_data["token"]
            self.token_expiry = expiry
            logger.info(f"Loaded valid token from cache (expires: {expiry})")
            return True

        except Exception as e:
            logger.debug(f"Failed to load token from cache: {e}")
            # Clean up corrupted cache file
            try:
                self._token_file.unlink()
            except Exception:
                pass
            return False

    def _save_token_to_cache(self):
        """Save the current token to cache."""
        if not self._token_file or not self.token or not self.token_expiry:
            return

        try:
            cache_data = {
                "token": self.token,
                "expiry": self.token_expiry.isoformat(),
                "username": self.username,
                "base_url": self.base_url,
                "cached_at": datetime.now().isoformat(),
            }

            # Ensure cache directory exists
            self._token_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first, then rename (atomic operation)
            temp_file = self._token_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(cache_data, f, indent=2)

            temp_file.replace(self._token_file)
            logger.info(f"Token saved to cache: {self._token_file}")

        except Exception as e:
            logger.warning(f"Failed to save token to cache: {e}")

    def authenticate_with_key(self, username, api_key):
        """
        Authenticate using username and API key.

        Args:
            username (str): The username
            api_key (str): The API key for authentication

        Returns:
            bool: True if authentication was successful

        Raises:
            AuthenticationError: If authentication fails
        """
        endpoint = f"{self.base_url}{ENDPOINTS['auth']['login_key']}"

        payload = {"userName": username, "apiKey": api_key}

        try:
            logger.info(f"Authenticating with API key for user: {username}")
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if not data.get("success", False):
                raise AuthenticationError(
                    f"Authentication failed: {data.get('errorMessage', 'Unknown error')}",
                    error_code=data.get("errorCode"),
                )

            self.token = data.get("token")
            self.token_expiry = datetime.now() + self.token_lifetime

            # Save token to cache
            self._save_token_to_cache()
            logger.info("Authentication successful, token cached")

            return True

        except requests.RequestException as e:
            raise AuthenticationError(f"Authentication request failed: {str(e)}")

    def authenticate_with_app(self, username, password, device_id, app_id, verify_key):
        """
        Authenticate using application credentials.

        Args:
            username (str): Admin username
            password (str): Admin password
            device_id (str): Device identifier
            app_id (str): Application identifier (GUID)
            verify_key (str): Verification key

        Returns:
            bool: True if authentication was successful

        Raises:
            AuthenticationError: If authentication fails
        """
        endpoint = f"{self.base_url}{ENDPOINTS['auth']['login_app']}"

        payload = {
            "userName": username,
            "password": password,
            "deviceId": device_id,
            "appId": app_id,
            "verifyKey": verify_key,
        }

        try:
            logger.info(f"Authenticating with app credentials for user: {username}")
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if not data.get("success", False):
                raise AuthenticationError(
                    f"Authentication failed: {data.get('errorMessage', 'Unknown error')}",
                    error_code=data.get("errorCode"),
                )

            self.token = data.get("token")
            self.token_expiry = datetime.now() + self.token_lifetime

            # Save token to cache
            self._save_token_to_cache()
            logger.info("Authentication successful, token cached")

            return True

        except requests.RequestException as e:
            raise AuthenticationError(f"Authentication request failed: {str(e)}")

    def validate_token(self):
        """
        Validate and renew the current token if needed.

        Returns:
            bool: True if validation was successful

        Raises:
            AuthenticationError: If validation fails
        """
        if not self.token:
            raise AuthenticationError("No token available for validation")

        endpoint = f"{self.base_url}{ENDPOINTS['auth']['validate']}"

        try:
            response = requests.post(
                endpoint, headers={"Authorization": f"Bearer {self.token}"}, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success", False):
                raise AuthenticationError(
                    f"Token validation failed: {data.get('errorMessage', 'Unknown error')}",
                    error_code=data.get("errorCode"),
                )

            # Update token if a new one was provided
            if "newToken" in data and data["newToken"]:
                self.token = data["newToken"]
                self.token_expiry = datetime.now() + self.token_lifetime
                # Save updated token to cache
                self._save_token_to_cache()
                logger.info("Token refreshed and cached")

            return True

        except requests.RequestException as e:
            raise AuthenticationError(f"Token validation request failed: {str(e)}")

    def get_token(self):
        """
        Get the current authentication token, validating if necessary.

        Returns:
            str: The current authentication token

        Raises:
            AuthenticationError: If no valid token is available
        """
        if not self.is_authenticated():
            if self.token:
                # Try to validate and refresh the token
                self.validate_token()
            else:
                raise AuthenticationError("No authentication token available")
        else:
            # Check if token is close to expiry (less than 30 minutes remaining)
            if self.token_expiry and (self.token_expiry - datetime.now() < timedelta(minutes=30)):
                # Validate to try and get a fresh token
                try:
                    self.validate_token()
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}")

        return self.token

    def get_auth_header(self):
        """
        Get the authentication header with a valid token.

        Returns:
            dict: The Authorization header with the bearer token

        Raises:
            AuthenticationError: If no valid token is available
        """
        token = self.get_token()
        return {"Authorization": f"Bearer {token}"}

    def is_authenticated(self):
        """
        Check if the client is currently authenticated with a valid token.

        Returns:
            bool: True if authenticated with a non-expired token
        """
        return (
            self.token is not None
            and self.token_expiry is not None
            and self.token_expiry > datetime.now()
        )

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the token cache status.

        Returns:
            dict: Cache information including directory, file existence, etc.
        """
        info = {
            "cache_enabled": self._cache_dir is not None,
            "cache_directory": str(self._cache_dir) if self._cache_dir else None,
            "token_file": str(self._token_file) if self._token_file else None,
            "token_file_exists": self._token_file.exists() if self._token_file else False,
        }

        # Add file modification time if file exists
        if info["token_file_exists"] and self._token_file:
            try:
                stat_result = self._token_file.stat()
                info["token_file_modified"] = datetime.fromtimestamp(stat_result.st_mtime).isoformat()
            except Exception:
                pass

        return info

    def clear_cache(self) -> bool:
        """
        Clear the token cache by removing the cache file.

        Returns:
            bool: True if cache was cleared successfully
        """
        if not self._token_file:
            logger.info("No cache file configured - nothing to clear")
            return True

        try:
            if self._token_file.exists():
                self._token_file.unlink()
                logger.info(f"Token cache cleared: {self._token_file}")
            else:
                logger.info("Token cache file does not exist - nothing to clear")

            # Clear in-memory token as well
            self.token = None
            self.token_expiry = None

            return True

        except Exception as e:
            logger.error(f"Failed to clear token cache: {e}")
            return False
