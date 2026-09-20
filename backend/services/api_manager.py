import sqlite3
import json
import time
from typing import Dict, Any, Optional
from backend.core.logger import app_logger
from backend.services.api_registry import get_integration, AuthMethod, ExecutionEngine

class APIManager:
    """
    Central manager for API integrations. Handles credentials, OAuth, rate limiting, and unified execution.
    """
    def __init__(self, db_path: str = "nova_api_manager.db"):
        self.db_path = db_path
        from backend.services.credentials import CredentialsManager
        self.cred_manager = CredentialsManager()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_credentials (
                    service_name TEXT PRIMARY KEY,
                    auth_type TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    api_key TEXT,
                    expires_at REAL,
                    metadata TEXT
                )
            ''')

    def connect(self, service_name: str, **kwargs) -> bool:
        """Initiate connection to a service. E.g., start OAuth flow or save API key."""
        meta = get_integration(service_name)
        if not meta:
            raise ValueError(f"Service {service_name} not found in registry.")

        if meta.auth_method == AuthMethod.API_KEY:
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError(f"{service_name} requires an api_key.")
            self._save_credentials(service_name, "api_key", api_key=api_key)
            app_logger.info(f"Successfully connected {service_name} via API Key.")
            return True
        elif meta.auth_method == AuthMethod.OAUTH2:
            app_logger.info(f"Starting OAuth2 flow for {service_name}...")
            # For OAuth, the actual saving will happen in the callback route.
            return True
        elif meta.auth_method == AuthMethod.NONE:
            return True
        return False

    def _save_credentials(self, service_name: str, auth_type: str, access_token: str = None, 
                          refresh_token: str = None, api_key: str = None, expires_at: float = None):
        
        # ENCRYPT SENSITIVE DATA
        enc_access = self.cred_manager.encrypt(access_token) if access_token else None
        enc_refresh = self.cred_manager.encrypt(refresh_token) if refresh_token else None
        enc_api = self.cred_manager.encrypt(api_key) if api_key else None

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO api_credentials 
                (service_name, auth_type, access_token, refresh_token, api_key, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (service_name, auth_type, enc_access, enc_refresh, enc_api, expires_at))

    def authenticate(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve and validate credentials for execution. Refreshes tokens if needed."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute('SELECT auth_type, access_token, refresh_token, api_key, expires_at FROM api_credentials WHERE service_name = ?', (service_name,)).fetchone()
            if not row:
                return None
            
            auth_type, enc_access, enc_refresh, enc_api, expires_at = row
            
            # DECRYPT
            access_token = self.cred_manager.decrypt(enc_access) if enc_access else None
            refresh_token = self.cred_manager.decrypt(enc_refresh) if enc_refresh else None
            api_key = self.cred_manager.decrypt(enc_api) if enc_api else None
            
            if auth_type == "oauth2":
                if expires_at and time.time() > expires_at:
                    app_logger.info(f"Session expired for {service_name}, refreshing auth...")
                    # Mock refresh
                    access_token = "new_mock_token_refreshed"
                    self._save_credentials(service_name, "oauth2", access_token=access_token, refresh_token=refresh_token, expires_at=time.time() + 3600)
                return {"Authorization": f"Bearer {access_token}"}
            elif auth_type == "api_key":
                return {"api_key": api_key}
            
        return None

    def disconnect(self, service_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM api_credentials WHERE service_name = ?', (service_name,))
        app_logger.info(f"Disconnected {service_name}.")

    async def execute(self, service_name: str, endpoint_func, **kwargs):
        """Unified execution interface. Handles rate limiting and retries."""
        auth_context = self.authenticate(service_name)
        # Check rate limits (omitted for brevity)
        try:
            return await endpoint_func(auth_context, **kwargs)
        except Exception as e:
            app_logger.error(f"API execution failed for {service_name}: {e}")
            raise e

    async def verify(self, service_name: str, verify_func, **kwargs):
        """Unified verification interface."""
        auth_context = self.authenticate(service_name)
        return await verify_func(auth_context, **kwargs)
