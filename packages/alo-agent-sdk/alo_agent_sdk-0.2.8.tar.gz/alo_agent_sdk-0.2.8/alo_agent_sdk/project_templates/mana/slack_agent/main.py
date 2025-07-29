import os
import asyncio
from dotenv import load_dotenv

from alo_agent_sdk.alo_a2a.server import A2AServer
from alo_agent_sdk.alo_a2a.models import AgentCard, AgentSkill, Task, TaskStatus, TaskState, Message, TextContent, MessageRole
from alo_agent_sdk.alo_a2a.mcp.manager import MCPManager, MCPConfigError, MCPAuthEnvError
from alo_agent_sdk.alo_a2a.mcp.client import MCPClientError
# from alo_agent_sdk.alo_a2a.discovery.server import enable_discovery # Discovery to be refactored for FastAPI
from alo_agent_sdk.alo_a2a.server.fastapi_server import run_fastapi_server

# Load environment variables from .env file if present (mainly for local development)
load_dotenv()

class SlackAgent(A2AServer):
    def __init__(self, agent_url: str):
        agent_card = AgentCard(
            name=os.getenv("AGENT_NAME", "SlackAgent"),
            description=os.getenv("AGENT_DESCRIPTION", "Un agente che invia messaggi a Slack tramite MCP"),
            url=agent_url,
            version=os.getenv("AGENT_VERSION", "1.0.0"),
            skills=[
                AgentSkill(
                    name="send_slack_message",
                    description="Invia un messaggio a un canale Slack specificato",
                    examples=[
                        "Invia 'Ciao team!' al canale #general",
                        "Scrivi 'Meeting alle 15:00' in #dev-team"
                    ],
                    tags=["slack", "messaging", "communication"]
                ),
                AgentSkill(
                    name="list_slack_channels",
                    description="Elenca i canali Slack disponibili",
                    examples=["Mostra tutti i canali", "Quali canali ci sono?"],
                    tags=["slack", "channels", "list"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
        self.mcp_manager = MCPManager() # MCPManager will load its config from default path or env vars
        self.slack_mcp_server_name = os.getenv("SLACK_MCP_SERVER_NAME", "slack-service")

    async def handle_task(self, task: Task) -> Task:
        try:
            message_text = ""
            if task.message and task.message.content and isinstance(task.message.content, TextContent):
                message_text = task.message.content.text.lower()
            
            if "send" in message_text and "slack" in message_text:
                result = await self._handle_send_message_from_task(task)
            elif "list" in message_text and "channel" in message_text:
                result = await self._handle_list_channels()
            else:
                result = "Comando non riconosciuto. Prova 'invia messaggio slack' o 'lista canali slack'."
            
            task.artifacts = [{"parts": [{"type": "text", "text": result}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            error_msg = f"Errore durante l'elaborazione del task: {str(e)}"
            task.artifacts = [{"parts": [{"type": "text", "text": error_msg}]}]
            task.status = TaskStatus(state=TaskState.FAILED, error=error_msg)
        return task
    
    async def _handle_send_message_from_task(self, task: Task) -> str:
        # Default values
        channel = "#general"
        message_to_send = "Messaggio di default dall'agente Slack."

        # Extract from task message if possible (simple parsing)
        if task.message and task.message.content and isinstance(task.message.content, TextContent):
            raw_text = task.message.content.text
            # Example: "invia 'testo del messaggio' al canale #canale"
            try:
                if "' al canale " in raw_text:
                    parts = raw_text.split("' al canale ", 1)
                    message_to_send = parts[0].split("'", 1)[1] if "'" in parts[0] else message_to_send
                    channel = parts[1].strip()
                elif "invia " in raw_text and " a " in raw_text: # "invia X a Y"
                    parts = raw_text.split(" a ", 1)
                    message_to_send = parts[0].replace("invia ", "").strip().strip("'\"")
                    channel = parts[1].strip()
            except Exception:
                pass # Stick to defaults if parsing fails

        # Override with task parameters if provided (more structured)
        if hasattr(task, 'parameters') and task.parameters:
            channel = task.parameters.get('channel', channel)
            message_to_send = task.parameters.get('message', task.parameters.get('text', message_to_send))
        
        return await self._send_slack_message_mcp(channel, message_to_send)
    
    async def _send_slack_message_mcp(self, channel: str, message: str) -> str:
        if not self.mcp_manager.is_server_configured(self.slack_mcp_server_name):
            return f"Errore: Server MCP '{self.slack_mcp_server_name}' non configurato. Impostare SLACK_MCP_SERVER_NAME se diverso."
        
        try:
            slack_client = await self.mcp_manager.get_client(self.slack_mcp_server_name)
            await slack_client.call_tool("send_message", channel=channel, text=message)
            return f"✅ Messaggio inviato a {channel} via MCP: '{message}'"
        except Exception as e:
            return f"❌ Errore invio messaggio Slack via MCP: {e}"
    
    async def _handle_list_channels(self) -> str:
        if not self.mcp_manager.is_server_configured(self.slack_mcp_server_name):
            return f"Errore: Server MCP '{self.slack_mcp_server_name}' non configurato."
        try:
            slack_client = await self.mcp_manager.get_client(self.slack_mcp_server_name)
            response = await slack_client.call_tool("list_channels") # Assumes tool exists
            return f"📋 Canali disponibili (via MCP): {response}"
        except Exception as e:
            return f"❌ Errore recupero canali Slack via MCP: {e}"
    
    async def cleanup(self):
        await self.mcp_manager.close_all_clients()

async def main():
    agent_host = os.getenv("AGENT_HOST", "0.0.0.0")
    agent_port = int(os.getenv("AGENT_PORT", "8003"))
    agent_url = os.getenv("AGENT_URL", f"http://{agent_host}:{agent_port}")
    # registry_url = os.getenv("REGISTRY_URL") # Discovery disabled for now

    agent = SlackAgent(agent_url=agent_url)
    
    print(f"🚀 Avvio {agent.agent_card.name} v{agent.agent_card.version} su {agent_url} con FastAPI")
    # print(f"MCP Config Path: {agent.mcp_manager.config_path}") # For debugging
    # print(f"Slack MCP Server Name: {agent.slack_mcp_server_name}") # For debugging

    # Discovery disabled for now as it's Flask-based in the current SDK
    # if registry_url:
    #     print(f"🔍 Tentativo di registrazione con registry: {registry_url}")
    #     try:
    #         discovery_client = enable_discovery(agent, registry_url=registry_url)
    #     except Exception as e:
    #         print(f"⚠️ Registrazione fallita o discovery non disponibile: {e}")
    # else:
    #     print("ℹ️ REGISTRY_URL non impostato, discovery non abilitata.")

    try:
        run_fastapi_server(agent, host=agent_host, port=agent_port, log_level="info")
    except KeyboardInterrupt:
        print(f"🛑 Arresto {agent.agent_card.name}...")
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
