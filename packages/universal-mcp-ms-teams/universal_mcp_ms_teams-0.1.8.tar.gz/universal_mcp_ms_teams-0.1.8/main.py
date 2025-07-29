import os
import pprint
from typing import Any

from loguru import logger

# Assuming the provided files (app.py, application.py, integration.py) are in a
# directory structure that Python can import from, e.g., universal_mcp/.
# If they are in the same directory, these imports will work.
from src.universal_mcp_ms_teams.app import MsTeamsApp
from universal_mcp.integrations import AgentRIntegration

# We'll need the AgentrClient from the utils module, which was referenced in integration.py
# For this example, we'll assume it exists and can be imported.
from universal_mcp.utils.agentr import AgentrClient


def main() -> None:
    """
    Initializes the MsTeamsApp using AgentR for authentication
    and calls the get_chats tool to test its functionality.
    """
    logger.info("Starting MS Teams App test...")

    # 1. Get AgentR configuration from environment variables
    #    You must set these in your environment before running the script.
    #    export AGENTR_BASE_URL="https://your-agentr-instance.com"
    #    export AGENTR_API_KEY="your-agentr-api-key"
    agentr_base_url = os.getenv("AGENTR_BASE_URL")
    agentr_api_key = os.getenv("AGENTR_API_KEY")

    if not agentr_base_url or not agentr_api_key:
        logger.error(
            "AGENTR_BASE_URL and AGENTR_API_KEY environment variables must be set."
        )
        return

    logger.info(f"Using AgentR base URL: {agentr_base_url}")

    try:
        # 2. Create the AgentR client
        agentr_client = AgentrClient(base_url=agentr_base_url, api_key=agentr_api_key)
        logger.success("AgentR client created successfully.")

        # 3. Create the AgentR integration for Microsoft Teams
        #    The name "ms-teams" must match the service name configured in your AgentR instance.
        ms_teams_integration = AgentRIntegration(
            name="ms-teams", client=agentr_client
        )
        logger.success("AgentR integration for 'ms-teams' initialized.")

        # 4. Initialize the MsTeamsApp with the integration
        #    The app will use this integration to fetch credentials (the access_token).
        ms_teams_app = MsTeamsApp(integration=ms_teams_integration)
        logger.success("MsTeamsApp initialized successfully.")

        # 5. Call the get_chats tool
        logger.info("Attempting to fetch chats using ms_teams_app.get_chats()...")
        chats: list[dict[str, Any]] = ms_teams_app.get_chats()
        logger.success(f"Successfully fetched {len(chats)} chats.")

        # 6. Print the results
        if chats:
            logger.info("Here are the details of the first 3 chats:")
            pprint.pprint(chats[:3])
        else:
            logger.info("No chats were found for the current user.")

    except Exception as e:
        logger.error(f"An error occurred during the test: {e}")
        # For debugging, you might want to see the full traceback
        # import traceback
        # traceback.print_exc()


if __name__ == "__main__":
    main()