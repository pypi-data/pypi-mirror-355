import os
import json
import requests
from werkzeug.security import generate_password_hash
from erioon.database import Database

class ErioonClient:
    """
    Client SDK for interacting with the Erioon API.

    Handles user authentication, token caching, and accessing user databases.

    Attributes:
        email (str): User email for login.
        password (str): User password for login.
        base_url (str): Base URL of the Erioon API.
        user_id (str | None): Authenticated user ID.
        error (str | None): Stores error messages if login fails.
        token_path (str): Local path to cached authentication token.
    """

    def __init__(self, api, email, password, base_url="https://sdk.erioon.com"):
        """
        Initialize ErioonClient instance, attempts to load cached token or perform login.

        Args:
            email (str): User email for authentication.
            password (str): User password for authentication.
            base_url (str, optional): Base API URL. Defaults to "https://sdk.erioon.com".
        """
        self.api = api
        self.email = email
        self.password = password
        self.base_url = base_url
        self.user_id = None
        self.error = None
        self.token_path = os.path.expanduser(f"~/.erioon_token_{self._safe_filename(email)}")

        try:
            metadata = self._load_or_login()
            self.user_id = metadata.get("_id")
            self.database = metadata.get("database")
            self.cluster = metadata.get("cluster")
            self.login_metadata = metadata
        except Exception as e:
            self.error = str(e)

    def _safe_filename(self, text):
        """
        Converts a string into a safe filename by replacing non-alphanumeric chars with underscores.

        Args:
            text (str): Input string to convert.

        Returns:
            str: Sanitized filename-safe string.
        """
        return "".join(c if c.isalnum() else "_" for c in text)

    def _do_login_and_cache(self):
        """
        Perform login to API and cache the metadata locally.

        Returns:
            dict: Login metadata including user_id, database, cluster.
        """
        metadata = self._login()
        with open(self.token_path, "w") as f:
            json.dump(metadata, f)
        return metadata

    def _load_or_login(self):
        """
        Load cached metadata or perform login.

        Returns:
            dict: Login metadata.
        """
        if os.path.exists(self.token_path):
            with open(self.token_path, "r") as f:
                metadata = json.load(f)
                if "user_id" in metadata:
                    return metadata

        return self._do_login_and_cache()

    def _login(self):
        """
        Authenticate and return full login metadata.

        Returns:
            dict: Metadata with user_id, database, cluster, etc.
        """
        url = f"{self.base_url}/login_with_credentials"
        payload = {"api_key": self.api,"email": self.email, "password": self.password}
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.login_metadata = data
            return data
        else:
            raise Exception("Invalid account")


    def _clear_cached_token(self):
        """
        Remove cached token file and reset user_id to None.
        """
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
        self.user_id = None

    def __getitem__(self, db_id):
        """
        Access a Database object by database ID.

        Args:
            db_id (str): The ID of the database to access.

        Returns:
            Database: An instance representing the database.

        Raises:
            ValueError: If client is not authenticated.
            Exception: For other API errors not related to database existence.

        Handles:
            On database-related errors, tries to relogin once. If relogin fails, returns "Login error".
            If database still not found after relogin, returns a formatted error message.
        """
        if not self.user_id:
            raise ValueError("Client not authenticated. Cannot access database.")
    
        try:
            return self._get_database_info(db_id)
        except Exception as e:
            err_msg = str(e).lower()
            if f"database with {db_id.lower()}" in err_msg or "database" in err_msg:
                self._clear_cached_token()
                try:
                    self.user_id = self._do_login_and_cache()
                except Exception:
                    return "Login error"
    
                try:
                    return self._get_database_info(db_id)
                except Exception:
                    return f"❌ Database with _id {db_id} ..."
            else:
                raise e
    
    def _get_database_info(self, db_id):
        """
        Helper method to fetch database info from API and instantiate a Database object.

        Args:
            db_id (str): The database ID to fetch.

        Returns:
            Database: Database instance with the fetched info.

        Raises:
            Exception: If API returns an error.
        """
        payload = {"user_id": self.user_id, "db_id": db_id}
        headers = {"Content-Type": "application/json"}

        response = requests.post(f"{self.base_url}/db_info", json=payload, headers=headers)

        if response.status_code == 200:
            db_info = response.json()
            return Database(
                user_id=self.user_id,
                metadata=db_info,
                database=self.database,
                cluster=self.cluster
            )
        else:
            try:
                error_json = response.json()
                error_msg = error_json.get("error", response.text)
            except Exception:
                error_msg = response.text
            raise Exception(error_msg)

    def __str__(self):
        """
        String representation: returns user_id if authenticated, else the error message.
        """
        return self.user_id if self.user_id else self.error

    def __repr__(self):
        """
        Developer-friendly string representation of the client instance.
        """
        return f"<ErioonClient user_id={self.user_id}>" if self.user_id else f"<ErioonClient error='{self.error}'>"
