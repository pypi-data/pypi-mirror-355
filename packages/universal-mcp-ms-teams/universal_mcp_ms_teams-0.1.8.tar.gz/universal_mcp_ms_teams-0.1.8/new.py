import httpx
from typing import Optional, List, Any, Dict

# Define a custom exception for HTTP status errors
class HTTPStatusError(httpx.HTTPStatusError):
    """
    Raised when the API request fails with detailed error information
    including status code and response body.
    """
    def __init__(self, message: str, request: httpx.Request, response: httpx.Response):
        super().__init__(message, request=request, response=response)
        self.status_code = response.status_code
        try:
            self.response_body = response.json()
        except httpx.ReadError:
            self.response_body = response.text


class GraphChatClient:
    """
    A client for interacting with the Microsoft Graph API for chat operations.
    """
    def __init__(self, access_token: str):
        """
        Initializes the GraphChatClient.

        Args:
            access_token (str): The OAuth 2.0 access token for authentication.
        """
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.access_token = access_token
        # Initialize httpx.Client for making HTTP requests
        # It's good practice to use a single client instance for multiple requests
        self.client = httpx.Client()

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """
        Makes an authenticated HTTP GET request.

        Args:
            url (str): The URL to make the GET request to.
            params (Optional[Dict[str, Any]]): Dictionary of query parameters.

        Returns:
            httpx.Response: The HTTP response object.
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        # Use the internal httpx client to make the request
        response = self.client.get(url, headers=headers, params=params)
        return response

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handles the HTTP response, raising an exception for errors or returning JSON.

        Args:
            response (httpx.Response): The HTTP response object.

        Returns:
            Dict[str, Any]: The JSON response body.

        Raises:
            HTTPStatusError: If the response indicates an error (status code >= 400).
        """
        if response.is_error:
            # Raise the custom HTTPStatusError if the request was not successful
            error_message = f"API request failed with status {response.status_code}"
            raise HTTPStatusError(error_message, request=response.request, response=response)
        
        # If the request was successful, parse and return the JSON response
        try:
            return response.json()
        except httpx.ReadError as e:
            raise ValueError(f"Failed to parse JSON response: {e}") from e

    def list_chats(
        self,
        top: Optional[int] = None,
        skip: Optional[int] = None,
        search: Optional[str] = None,
        filter: Optional[str] = None,
        count: Optional[bool] = None,
        orderby: Optional[List[str]] = None,
        select: Optional[List[str]] = None,
        expand: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        List chats

        Args:
            top (integer): Show only the first n items. Example: '50'.
            skip (integer): Skip the first n items.
            search (string): Search items by search phrases.
            filter (string): Filter items by property values.
            count (boolean): Include count of items.
            orderby (array): Order items by property values.
            select (array): Select properties to be returned.
            expand (array): Expand related entities.

        Returns:
            dict[str, Any]: Retrieved collection of chats.

        Raises:
            HTTPStatusError: Raised when the API request fails with detailed error information
                             including status code and response body.

        Tags:
            chats.chat, important
        """
        url = f"{self.base_url}/chats"

        # Build query parameters, filtering out None values
        query_params = {
            k: v for k, v in [
                ('$top', top),
                ('$skip', skip),
                ('$search', search),
                ('$filter', filter),
                ('$count', 'true' if count else None), # Microsoft Graph requires '$count=true'
                ('$orderby', ','.join(orderby) if orderby else None),
                ('$select', ','.join(select) if select else None),
                ('$expand', ','.join(expand) if expand else None)
            ] if v is not None
        }

        # Make the GET request using the internal helper method
        response = self._get(url, params=query_params)
        
        # Handle the response and return the JSON data
        return self._handle_response(response)

# Example Usage (replace "YOUR_ACCESS_TOKEN" with an actual token)
if __name__ == "__main__":
    # IMPORTANT: Replace this with your actual access token.
    # You would typically obtain this token via an OAuth 2.0 flow (e.g., Azure AD).
    # For testing, you might use a token obtained manually if you have one.
    ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJub25jZSI6IndyYzhXUnR6QmtSNGFqRFBkd2NWczdDMlZrc1V2X2luRVpWSUxPRE1YemciLCJhbGciOiJSUzI1NiIsIng1dCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSIsImtpZCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSJ9.eyJhdWQiOiIwMDAwMDAwMy0wMDAwLTAwMDAtYzAwMC0wMDAwMDAwMDAwMDAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC84Njc3NTEwNi0wYTlmLTRhYjEtOTY0OC02MDBiMTJjYmM3YWQvIiwiaWF0IjoxNzQ5NzUzMDM0LCJuYmYiOjE3NDk3NTMwMzQsImV4cCI6MTc0OTc1ODE5MywiYWNjdCI6MCwiYWNyIjoiMSIsImFpbyI6IkFYUUFpLzhaQUFBQTNnaTMwOHR1SUtJNVZOUlhhbDJ4emYrSkk4b0F4WVRJb1loOHoydzIyaEFYZENseVE2U2NtRkVWcTRhQllYbEFJUnBQaXh2Q01pZzN2RngzVjBTSm5WYlZlQVFoSjIydndMeFMrRUNxeVdRQWhwa1hNWnFPTGdqazVvdnhKNnNEbXBDRi9xVHRVWDduVnFtMHgwSzNodz09IiwiYW1yIjpbInB3ZCJdLCJhcHBfZGlzcGxheW5hbWUiOiJBZ2VudFIgRGV2IiwiYXBwaWQiOiIyNjQ1ZjZkNS1kYmY0LTQ4ZDItYWQyMS1iNWEwOWVkMzBhZjMiLCJhcHBpZGFjciI6IjEiLCJmYW1pbHlfbmFtZSI6IlJhbmphbiIsImdpdmVuX25hbWUiOiJBbmtpdCIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjExNy4yNTAuMTYxLjIyMiIsIm5hbWUiOiJBbmtpdCBSYW5qYW4iLCJvaWQiOiJlMmJlZWMyYy1mNTViLTQ2OTEtOGJjNi0yOGRmZmQyMWEwOGMiLCJwbGF0ZiI6IjUiLCJwdWlkIjoiMTAwMzIwMDQ3QkI2M0NGMiIsInJoIjoiMS5BYjRBQmxGM2hwOEtzVXFXU0dBTEVzdkhyUU1BQUFBQUFBQUF3QUFBQUFBQUFBQjdBZDItQUEuIiwic2NwIjoiQ2hhbm5lbC5SZWFkQmFzaWMuQWxsIENoYW5uZWxNZXNzYWdlLkVkaXQgQ2hhbm5lbE1lc3NhZ2UuU2VuZCBDaGF0LkNyZWF0ZSBDaGF0LlJlYWQgQ2hhdC5SZWFkQmFzaWMgQ2hhdC5SZWFkV3JpdGUgQ2hhdE1lc3NhZ2UuUmVhZCBDaGF0TWVzc2FnZS5TZW5kIEZpbGVzLlJlYWQuQWxsIEZpbGVzLlJlYWRXcml0ZS5BbGwgRmlsZXMuUmVhZFdyaXRlLkFwcEZvbGRlciBNYWlsLlJlYWQgTWFpbC5SZWFkV3JpdGUgTWFpbC5TZW5kIFNpdGVzLkZ1bGxDb250cm9sLkFsbCBTaXRlcy5SZWFkV3JpdGUuQWxsIFRlYW0uQ3JlYXRlIFRlYW0uUmVhZEJhc2ljLkFsbCBUZWFtc0FjdGl2aXR5LlJlYWQgVGVhbXNBY3Rpdml0eS5TZW5kIFRlYW1zVGFiLlJlYWRXcml0ZUZvclVzZXIgVGVhbXNUYWIuUmVhZFdyaXRlU2VsZkZvclVzZXIgVXNlci5SZWFkIHByb2ZpbGUgb3BlbmlkIGVtYWlsIiwic2lkIjoiMDA1YmUzODktMGFkZC02ZmJkLTE5ODYtZGUyZGRlNGNkZjhiIiwic2lnbmluX3N0YXRlIjpbImttc2kiXSwic3ViIjoidk41a2FzYzVtWUp2VTJheXg3LW1EaF9QSHkxUDk2Y0xnWFhuMTcycjZwayIsInRlbmFudF9yZWdpb25fc2NvcGUiOiJBUyIsInRpZCI6Ijg2Nzc1MTA2LTBhOWYtNGFiMS05NjQ4LTYwMGIxMmNiYzdhZCIsInVuaXF1ZV9uYW1lIjoiYW5raXRAYWdlbnRyLmRldiIsInVwbiI6ImFua2l0QGFnZW50ci5kZXYiLCJ1dGkiOiJlTTdQQldWeURFcU1QYjRGYlhYQUFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX2Z0ZCI6ImY4SVdOQTBJSkxCcDd5U3U3T0xWVDYzeE5ES2FKNjgxUUh4TGZRamVCcGNCYW1Gd1lXNWxZWE4wTFdSemJYTSIsInhtc19pZHJlbCI6IjEgMiIsInhtc19zdCI6eyJzdWIiOiI0Y0xWREg1VGxiVUp6N2poRTZHeEhjUjBSdTd6Z3B6TUU1YlRTTzFGVzBnIn0sInhtc190Y2R0IjoxNzQzODY1Mjc5fQ.gzPD0AvMpSsSsjxqrFYO4a9ZrHVKctnH_QF1EEZODL1oOdnl7QpTUicq5G8nJL59JlIEHwCA0yNO7zNdYCnswKtLyx5prm3KPY8dC6l8a6v9udopNodKejfarEbkdQmFfx1zcnWwEIPbmS4rloFCOHCW29YiFupi4z5ir29uu4KAiNOysH7I6XY-eJQFjG9LbHloY9pVl4feWyYmuFj_JuI0COzLYGvtfdMsH9kzq1OYyMEXtce5Q7CBUkhjqDP8P6BRadPcfd5ECKvUX_QQllkjJBFRj4LjmU2lQdUZn4ijpsm3EPKUouByOwy25g404rPbFqTwNqeLoc7xVlQBAA"
    
    if ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
        print("WARNING: Please replace 'YOUR_ACCESS_TOKEN' with a valid access token.")
        print("This example will not work without a real access token.")
        print("Refer to Microsoft Graph authentication documentation for obtaining a token.")
    else:
        try:
            client = GraphChatClient(access_token=ACCESS_TOKEN)

            print("Attempting to list chats (first 5)...") # Updated print statement
            chats_data = client.list_chats(
                top=5,
                # Removed orderby parameter as it's not supported for createdDateTime
                select=["id", "topic", "chatType", "createdDateTime"],
                expand=["members"] # Example of expanding members
            )
            
            print("\nSuccessfully retrieved chats:")
            for chat in chats_data.get('value', []):
                print(f"  Chat ID: {chat.get('id')}")
                print(f"  Topic: {chat.get('topic') or 'N/A'}")
                print(f"  Type: {chat.get('chatType')}")
                print(f"  Created: {chat.get('createdDateTime')}")
                if chat.get('members'):
                    print(f"  Members count: {len(chat['members'])}")
                print("-" * 20)

            # Example with a filter (e.g., chats created after a certain date)
            # You'll need to adjust the date for actual chats in your tenant
            # print("\nAttempting to list chats created after 2024-01-01T00:00:00Z...")
            # filtered_chats = client.list_chats(filter="createdDateTime ge 2024-01-01T00:00:00Z")
            # print(f"Found {len(filtered_chats.get('value', []))} chats created after the specified date.")

        except HTTPStatusError as e:
            print(f"\nError listing chats: {e}")
            print(f"Status Code: {e.status_code}")
            print(f"Response Body: {e.response_body}")
        except ValueError as e:
            print(f"\nData processing error: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")

