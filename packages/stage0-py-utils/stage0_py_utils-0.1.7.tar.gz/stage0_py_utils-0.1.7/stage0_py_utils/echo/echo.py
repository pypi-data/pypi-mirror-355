import asyncio
import json
import re
from stage0_py_utils.echo.agent import Agent
from stage0_py_utils.echo.discord_bot import DiscordBot
from stage0_py_utils.echo.llm_handler import LLMHandler
from stage0_py_utils.echo.ollama_llm_client import OllamaLLMClient

import logging
logger = logging.getLogger(__name__)

class Echo:
    """_summary_
    The Echo class is the container that coordinates
    action between the discord_bot and llm_handler. 
    Agents register their actions with Echo, and Echo
    implements the handle_command function used in
    those classes to execute agent/actions.
    """
    ECHO_AGENT_COMMAND_PATTERN = re.compile(r"^/([^/]+)/([^/]+)(?:/(.*))?$")
    
    def __init__(self, name=None, bot_id=None, model=None, client=None):
        """Initialize Echo with a default agents."""
        self.name = name
        self.model = model
        self.agents = {}        
        self.llm_client = client or OllamaLLMClient(model=model)

        # Register default agents
        from stage0_py_utils.agents.bot_agent import create_bot_agent
        from stage0_py_utils.agents.conversation_agent import create_conversation_agent
        from stage0_py_utils.agents.echo_agent import create_echo_agent
        self.register_agent(create_echo_agent(agent_name="echo", echo=self))
        self.register_agent(create_bot_agent(agent_name="bot"))
        self.register_agent(create_conversation_agent(agent_name="conversation"))

        # Initialize LLM Conversation Handler
        self.llm_handler = LLMHandler(
            echo_bot_name=self.name,
            handle_command_function=self.handle_command, 
            llm_client=self.llm_client
        )
        # Initialize Discord Chatbot
        self.bot = DiscordBot(
            handle_command_function=self.handle_command, 
            handle_message_function=self.llm_handler.handle_message,
            bot_id=bot_id
        )
        
    def register_default_routes(self, app=None):
        from stage0_py_utils import create_bot_routes
        from stage0_py_utils import create_conversation_routes
        from stage0_py_utils import create_echo_routes
        app.register_blueprint(create_bot_routes(), url_prefix='/api/bot')
        app.register_blueprint(create_conversation_routes(), url_prefix='/api/conversation')
        app.register_blueprint(create_echo_routes(echo=self), url_prefix='/api/echo')    
        return
    
    def run(self, token):
        self.bot.run(token)
   
    def close(self, timeout=2):
        """
        Gracefully shut down the Discord bot, and handle the 
        asynchronous nature of Client.close() without hanging.
        """
        logger.info("Closing Discord Bot connection...")

        try:
            # Check if an event loop is already running
            loop = asyncio.get_running_loop()  
            future = asyncio.run_coroutine_threadsafe(self.bot.close(), loop)
            future.result(timeout=timeout)  # Wait for close() to finish
        except RuntimeError:
            # No active event loop found. Creating a new one.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.bot.close())  
            loop.close()  # Clean up the event loop
        except TimeoutError:
            logger.info(f"Discord Client.close() timed out after {timeout} seconds")
                                    
    def register_agent(self, agent=None):
        """Registers an agent with Echo."""
        if not isinstance(agent, Agent): 
            raise Exception(f"can not register agent without actions: {agent}")
        self.agents[agent.name] = agent

    def get_agents(self):
        """Returns a list of registered agent names."""
        the_agents = []
        for agent_key in self.agents:
            agent = self.agents[agent_key]
            agent_info = {
                "agent_name": agent_key,
                "description": agent.description,
                "actions": []
            }
            for action_key in agent.actions:
                action = agent.actions[action_key]
                action_info = {
                    "action_name": action_key,
                    "description": action["description"]
                }
                agent_info["actions"].append(action_info)
                
            the_agents.append(agent_info)
        return the_agents

    def get_action(self, agent_name=None, action_name=None):
        """Returns a a registered agent."""
        if agent_name not in self.agents:
            logger.info(f"Agent {agent_name} not found")
            return "Invalid Agent"

        agent = self.agents[agent_name]
        if action_name not in agent.get_actions():
            logger.info(f"Action {action_name} not found")
            return "Invalid Action"
        
        action = agent.actions[action_name]
        return {
            "action_name": action_name, 
            "description": action["description"],
            "arguments_schema": action["arguments_schema"],
            "output_schema": action["output_schema"]
        }

    def parse_command(self, command: str):
        """
        Parses a command in the format: /agent/action/arguments.
        Ensures only the first two slashes separate agent and action, 
        while keeping the arguments intact.
        """
        match = self.ECHO_AGENT_COMMAND_PATTERN.match(command)
        if not match:
            logger.warning(f"Invalid Command Requested {command}")
            raise Exception(f"Invalid command format: {command}")

        agent_name, action_name, arguments_str = match.groups()

        # Parse JSON safely
        try:
            arguments = json.loads(arguments_str) if arguments_str else None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON Arguments {arguments_str}")
            raise Exception(f"Invalid JSON in arguments: {arguments_str}") from e

        return agent_name, action_name, arguments
    
    def handle_command(self, command: str):
        """
        Handles an incoming command.
        - Routes it to the correct agent and action.
        - Returns the response from the agent.
        - If invalid, returns an error message or silence (for unknown agents).
        """
        try:
            agent_name, action_name, arguments = self.parse_command(command)
        except Exception as e:
            return f"Invalid Command Format {e}"

        if agent_name not in self.agents:
            logger.debug(f"Agent {agent_name} not found")
            return f"Unknown Agent {agent_name}. Available agents are: {self.agents.keys}"
        
        agent = self.agents[agent_name]

        if action_name not in agent.get_actions():
            available_actions = ", ".join(agent.get_actions())
            return f"Unknown action '{action_name}'. Available actions: {available_actions}"

        output  = agent.invoke_action(action_name, arguments)
        return output
