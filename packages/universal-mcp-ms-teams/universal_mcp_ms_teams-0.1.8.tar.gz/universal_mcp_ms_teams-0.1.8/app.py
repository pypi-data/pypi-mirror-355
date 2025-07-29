import httpx
from typing import Any

from universal_mcp.applications import APIApplication
from universal_mcp.integrations import Integration


class MsTeamsApp(APIApplication):
    """
    Application for interacting with the Microsoft Teams API via the Microsoft Graph.
    Provides tools for managing teams, channels, chats, and messages.
    """

    def __init__(self, integration: Integration) -> None:
        """
        Initializes the MicrosoftTeamsApp.

        Args:
            integration: An Integration object that provides the necessary
                         authentication credentials (access_token) for the Microsoft Graph API.
        """
        super().__init__(name="ms-teams", integration=integration)
        self.base_url = "https://graph.microsoft.com/v1.0"

    def get_joined_teams(self) -> list[dict[str, Any]]:
        """
        Fetches a list of the Microsoft Teams the user has joined.

        Returns:
            A list of dictionaries, where each dictionary represents a team.

        Raises:
            httpx.HTTPStatusError: If the API request fails due to authentication or other issues.

        Tags:
            read, list, teams, microsoft-teams, api
        """
        url = f"{self.base_url}/me/joinedTeams"
        response = self._get(url)
        data = self._handle_response(response)
        # The API returns the list of teams under the "value" key.
        return data.get("value", [])

    def list_channels_for_team(self, team_id: str) -> list[dict[str, Any]]:
        """
        Fetches the list of channels within a specific Microsoft Teams team.

        Args:
            team_id: The unique identifier of the team.

        Returns:
            A list of dictionaries, where each dictionary represents a channel.

        Raises:
            httpx.HTTPStatusError: If the API request fails, e.g., team not found.

        Tags:
            read, list, channels, microsoft-teams, api
        """
        url = f"{self.base_url}/teams/{team_id}/channels"
        response = self._get(url)
        data = self._handle_response(response)
        # The API returns the list of channels under the "value" key.
        return data.get("value", [])



    def send_channel_message(self, team_id: str, channel_id: str, content: str) -> dict[str, Any]:
        """
        Sends a message to a specific channel in a Microsoft Teams team.

        Args:
            team_id: The unique identifier of the team.
            channel_id: The unique identifier of the channel within the team.
            content: The message content to send (can be plain text or HTML).

        Returns:
            A dictionary containing the API response for the sent message, including its ID.

        Raises:
            httpx.HTTPStatusError: If the API request fails due to invalid IDs, permissions, etc.

        Tags:
            create, send, message, channel, microsoft-teams, api, important
        """
        url = f"{self.base_url}/teams/{team_id}/channels/{channel_id}/messages"
        payload = {"body": {"content": content}}
        response = self._post(url, data=payload)
        return self._handle_response(response)

    def send_chat_message(self, chat_id: str, content: str) -> dict[str, Any]:
        """
        Sends a message to a specific chat.

        Args:
            chat_id: The unique identifier of the chat.
            content: The message content to send (can be plain text or HTML).

        Returns:
            A dictionary containing the API response for the sent message, including its ID.

        Raises:
            httpx.HTTPStatusError: If the API request fails due to invalid ID, permissions, etc.

        Tags:
            create, send, message, chat, microsoft-teams, api, important
        """
        url = f"{self.base_url}/chats/{chat_id}/messages"
        payload = {"body": {"content": content}}
        response = self._post(url, data=payload)
        return self._handle_response(response)

    def reply_to_channel_message(self, team_id: str, channel_id: str, message_id: str, content: str) -> dict[str, Any]:
        """
        Sends a reply to a specific message in a channel.

        Args:
            team_id: The unique identifier of the team.
            channel_id: The unique identifier of the channel.
            message_id: The unique identifier of the message to reply to.
            content: The reply message content (can be plain text or HTML).

        Returns:
            A dictionary containing the API response for the sent reply, including its ID.

        Raises:
            httpx.HTTPStatusError: If the API request fails due to invalid IDs, permissions, etc.

        Tags:
            create, send, reply, message, channel, microsoft-teams, api, important
        """
        url = f"{self.base_url}/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies"
        payload = {"body": {"content": content}}
        response = self._post(url, data=payload)
        return self._handle_response(response)

    def list_tools(self) -> list[callable]:
        """Lists all the callable tool methods available in the MicrosoftTeamsApp."""
        return [
            self.get_joined_teams,
            self.get_channels,
            self.get_chats,
            self.send_channel_message,
            self.send_chat_message,
            self.reply_to_channel_message,
        ]
