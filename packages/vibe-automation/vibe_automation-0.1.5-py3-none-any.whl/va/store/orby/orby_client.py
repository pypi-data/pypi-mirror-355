import webbrowser
from datetime import datetime, timedelta, timezone
from typing import Optional
from requests_oauthlib import OAuth2Session
from http import HTTPStatus
from dotenv import load_dotenv
from va.store.orby.http.server import OAuthCallbackServer
from va.utils.auth import Credential, save_credential, get_credential
import os

load_dotenv(".env.dev")


class OrbyClient:
    """Singleton OAuth client for Orby API calls with automatic token management"""

    _instance = None

    def __init__(self):
        if OrbyClient._instance is not None:
            raise RuntimeError(
                "OrbyClient is a singleton. Use OrbyClient.get_instance() instead."
            )
        # Initialize base_url and client_id from environment variables
        self.base_url = os.getenv("ORBY_BASE_URL", "https://grpc.orby.ai")
        self.client_id = os.getenv("ORBY_CLIENT_ID", "<placeholder>")
        self._session: Optional[OAuth2Session] = None
        self._credential: Optional[Credential] = None
        self._load_credential()

    @classmethod
    def get_instance(cls) -> "OrbyClient":
        """Get the singleton instance of OrbyClient"""
        if cls._instance is None:
            instance = cls.__new__(cls)
            instance.__init__()
            cls._instance = instance
        return cls._instance

    def _load_credential(self):
        """Load credential from file"""
        self._credential = get_credential()
        if self._credential:
            self._session = OAuth2Session(
                self.client_id, token=self._credential.to_dict()
            )

    def is_authenticated(self) -> bool:
        """Check if client has valid credentials"""
        return self._credential is not None and not self._is_token_expired()

    def _is_token_expired(self) -> bool:
        """Check if current token is expired or will expire soon"""
        if not self._credential or not self._credential.expiry:
            return True
        try:
            expiry_dt = datetime.fromisoformat(self._credential.expiry)
            now = datetime.now(timezone.utc)
            # Consider expired if expires in less than 1 minute
            return expiry_dt < now or (expiry_dt - now) < timedelta(minutes=1)
        except ValueError:
            return True

    def _refresh_token(self) -> bool:
        """Refresh the access token using refresh token"""
        if not self._credential or not self._credential.refresh_token:
            return False

        try:
            # Create a new session with the current credentials
            session = OAuth2Session(self.client_id, token=self._credential.to_dict())

            new_token = session.refresh_token(
                f"{self.base_url}/oauth2/token",
                client_id=self.client_id,
                refresh_token=self._credential.refresh_token,
            )
            # Update credential with new token info
            self._credential.access_token = new_token.get(
                "access_token", self._credential.access_token
            )
            self._credential.token_type = new_token.get(
                "token_type", self._credential.token_type
            )
            self._credential.refresh_token = new_token.get(
                "refresh_token", self._credential.refresh_token
            )
            self._credential.expiry = new_token.get("expiry", self._credential.expiry)
            # Save updated credential
            save_credential(self._credential)

            # Update session
            self._session = OAuth2Session(
                self.client_id, token=self._credential.to_dict()
            )

            return True

        except Exception as e:
            print(f"Failed to refresh token: {e}")
            return False

    def login(self, force: bool = False) -> bool:
        """
        Perform OAuth login flow

        Args:
            force: If True, force new login even if already authenticated

        Returns:
            True if login successful, False otherwise
        """
        # Check if already authenticated and not forcing
        if not force and self.is_authenticated():
            return True

        # Try to refresh token first, if it's needed.
        if not force and self._credential and self._refresh_token():
            return True

        # Perform full OAuth flow
        return self._perform_oauth_flow()

    def _perform_oauth_flow(self) -> bool:
        """Perform the complete OAuth authorization flow"""
        server = OAuthCallbackServer()

        # Retrieve the redirect URL from the authorization endpoint.
        def get_redirect_url(session: OAuth2Session) -> str:
            auth_url, _ = session.authorization_url(f"{self.base_url}/oauth2/authorize")
            response = session.get(auth_url, allow_redirects=False)
            if not HTTPStatus(response.status_code).is_redirection:
                print(f"OAuth error: Unexpected status {response.status_code}")
                return ""
            return response.url

        try:
            # Step 1: Start the callback server.
            server.start()

            # Step 2: Create an OAuth session.
            session = OAuth2Session(
                self.client_id,
                redirect_uri=f"http://{server.host}:{server.port}/oauth/callback",
                scope="all",
                pkce="S256",
            )

            # Step 3: Get the authorization redirect URL.
            redirect_url = get_redirect_url(session)
            if not redirect_url:
                return False

            # Step 4: Open the browser for authorization.
            webbrowser.open(redirect_url)
            print("⏳ Waiting for authorization...")
            print(
                "If browser doesn't open, visit this URL to authorize: ", redirect_url
            )

            # Step 5: Wait for the authorization callback to receive the code.
            code = server.wait_for_callback()
            if not code:
                return False
            print(f"Code: {code}")

            # Step 6: Exchange the code for an access token.
            token = session.fetch_token(
                token_url=f"{self.base_url}/oauth2/token",
                client_id=self.client_id,
                code=code,
                include_client_id=True,
            )
            print(f"Token: {token}")

            # Step 7: Save the credentials and update the session.
            self._credential = Credential(**token)
            save_credential(self._credential)
            self._session = OAuth2Session(
                self.client_id, token=self._credential.to_dict()
            )

            return True

        except Exception as e:
            print(f"OAuth flow failed: {e}")
            return False

        finally:
            server.stop()


# Convenience function to get the singleton instance
def get_orby_client() -> OrbyClient:
    """Get the OrbyClient singleton instance"""
    return OrbyClient.get_instance()
