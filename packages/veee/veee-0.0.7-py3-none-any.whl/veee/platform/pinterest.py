# Copyright 2025 Clivern
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import requests
from veee.platform.integration import Integration


class Pinterest(Integration):
    """
    Pinterest Platform
    """

    def __init__(self, config: dict):
        """
        Initialize the Pinterest platform

        Args:
            config (dict): The configuration
        """
        self._app_id = config.get("app_id")
        self._app_secret = config.get("app_secret_key")
        self._app_redirect_uri = config.get("app_redirect_uri")
        self._app_scope = config.get(
            "app_scope", "boards:read,pins:read,pins:write,user_accounts:read,boards:write"
        )
        self._response_type = config.get("response_type", "code")
        self._api_url = "https://api.pinterest.com/v5"
        self._api_oauth_url = "https://www.pinterest.com/oauth/"

    def get_oauth_redirect_url(self, data: dict) -> str:
        """
        Get the OAuth redirect URL

        Args:
            data (dict): The data to be used to generate the OAuth redirect URL

        Returns:
            str: The OAuth redirect URL
        """
        state = data.get("state", "")

        return f"{self._api_oauth_url}?client_id={self._app_id}&redirect_uri={self._app_redirect_uri}&response_type={self._response_type}&scope={self._app_scope}&state={state}"

    def get_access_tokens(self, data: dict) -> dict:
        """
        Get the access tokens (access_token, refresh_token, expires_in)

        Args:
            data (dict): The data to be used to get the access tokens

        Returns:
            dict: The access tokens
                {
                    "access_token": "{access_token_string_with_'pina'_prefix}",
                    "refresh_token": "{refresh_token_string_with_'pinr'_prefix}",
                    "response_type": "authorization_code",
                    "token_type": "bearer",
                    "expires_in": 2592000,
                    "refresh_token_expires_in": 31536000,
                    "scope": "boards:read boards:write pins:read"
                }
        """
        code = data.get("code", "")

        response = requests.post(
            f"{self._api_url}/oauth/token",
            headers={
                "Authorization": f"Basic {base64.b64encode(f'{self._app_id}:{self._app_secret}'.encode('utf-8')).decode('utf-8')}"
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._app_redirect_uri,
                "continuous_refresh": "true",
            },
        )

        return response.json()

    def get_user_info(self, access_token: str) -> dict:
        """
        Get the user info

        Args:
            access_token (str): The access token

        Returns:
            dict: The user info
        """
        response = requests.get(
            f"{self._api_url}/user_account",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()

    def rotate_access_tokens(self, refresh_token: str) -> dict:
        """
        Rotate the access tokens

        Args:
            refresh_token (str): The refresh token

        Returns:
            dict: The access tokens
                {
                    "access_token": "{access_token_string_with_'pina'_prefix}",
                    "refresh_token": "{refresh_token_string_with_'pinr'_prefix}",
                    "response_type": "authorization_code",
                    "token_type": "bearer",
                    "expires_in": 2592000,
                    "refresh_token_expires_in": 31536000,
                    "scope": "boards:read boards:write pins:read"
                }
        """
        response = requests.post(
            f"{self._api_url}/oauth/token",
            headers={
                "Authorization": f"Basic {base64.b64encode(f'{self._app_id}:{self._app_secret}'.encode('utf-8')).decode('utf-8')}"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": self._app_scope,
            },
        )
        return response.json()

    def post_message(self, access_token: str, message: dict) -> dict:
        """Post a message to the integration"""
        return {"status": "success"}

    def _get_boards(self, access_token: str) -> list:
        """
        Get the boards

        Args:
            access_token (str): The access token

        Returns:
            list: The boards
        """
        response = requests.get(
            f"{self._api_url}/boards",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()

    def post(self, access_token: str, message: dict) -> dict:
        """Post a message to the integration"""
        return {"status": "success"}

    def version(self) -> str:
        return "0.0.1"
