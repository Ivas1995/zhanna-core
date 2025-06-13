import asyncio
from typing import Dict, Callable
from config import CONFIG
from plugins import zhanna, xai, openai, youtube, search
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler

class AgentOrchestrator:
    def __init__(self):
        self.agents: Dict[str, Agent] = {
            "trading": Agent("TradingAgent", self.handle_trading),
            "code_improvement": Agent("CodeImprovementAgent", self.handle_code_improvement),
            "search": Agent("SearchAgent", self.handle_search),
            "media": Agent("MediaAgent", self.handle_media)
        }

    async def handle_trading(self, command: str, user_id: str) -> str:
        from crypto_trader import execute_trade
        return await execute_trade(command, user_id)

    async def handle_code_improvement(self, command: str, user_id: str) -> str:
        from plugins.self_improvement import improve_code
        return await improve_code()

    async def handle_search(self, command: str, user_id: str) -> str:
        from plugins.search import search_query
        return await search_query(command, user_id)

    async def handle_media(self, command: str, user_id: str) -> str:
        from plugins.youtube import play_youtube
        return await play_youtube(command, user_id)

    async def process_command(self, command: str, user_id: str) -> str:
        """Route command to appropriate agent."""
        command_lower = command.lower()
        for agent_name, agent in self.agents.items():
            if agent_name in command_lower:
                return await agent.handler(command, user_id)
        # Default to xAI for general queries
        return await xai.request_xai(command, mode="deepsearch")

    async def run_background_tasks(self):
        """Run background tasks for all agents."""
        tasks = [
            self.agents["trading"].handler("analyze market", "system"),
            self.agents["code_improvement"].handler("", "system")
        ]
        await asyncio.gather(*tasks)

orchestrator = AgentOrchestrator()