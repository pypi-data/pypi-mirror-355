from universal_mcp.integrations import AgentRIntegration
from universal_mcp_ms_teams.app import MsTeamsApp
from universal_mcp.tools import ToolManager
import anyio

integration = AgentRIntegration(name="ms-teams", base_url="https://api.agentr.dev")
app_instance = MsTeamsApp(integration=integration)

tool_manager = ToolManager()
tool_manager.add_tool(app_instance.get_chats)
# result = anyio.run(tool_manager.call_tool(name="get_chats", arguments={}))


# print(result)

async def main():
    result = await tool_manager.call_tool(name="get_chats", arguments={})
    print(result)
    
if __name__ == "__main__":
    anyio.run(main)