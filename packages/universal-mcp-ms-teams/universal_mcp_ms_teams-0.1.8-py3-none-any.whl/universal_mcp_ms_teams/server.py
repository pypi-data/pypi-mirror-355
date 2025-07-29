
from pathlib import Path
from universal_mcp.servers import SingleMCPServer
from universal_mcp.integrations import AgentRIntegration
from universal_mcp.stores import EnvironmentStore
from universal_mcp_ms_teams.app import MsTeamsApp

env_store = EnvironmentStore()
integration_instance = AgentRIntegration(name="microsoft-teams", store=env_store, base_url="https://api.agentr.dev")
app_instance = MsTeamsApp(integration=integration_instance)

mcp = SingleMCPServer(
    app_instance=app_instance,
)

if __name__ == "__main__":
    mcp.run()


