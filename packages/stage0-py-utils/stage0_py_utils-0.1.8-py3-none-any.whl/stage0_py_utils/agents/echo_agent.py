import logging
from stage0_py_utils.echo.agent import Agent
from stage0_py_utils.echo.echo import Echo
from stage0_py_utils.echo_utils.token import create_echo_token
from stage0_py_utils.echo_utils.breadcrumb import create_echo_breadcrumb

logger = logging.getLogger(__name__)

def create_echo_agent(agent_name, echo=None):
    """ Registers event handlers and commands for the Config Agent. """
    if not isinstance(echo, Echo):
        raise Exception("create_echo_agent Error: an instance of Echo is a required parameter")
    agent = Agent(name=agent_name, description="The echo agent get's meta-data about agents and actions")
    
    def get_agents(arguments):
        """ Slash command to get agent data"""
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            agents = echo.get_agents()
            logger.info(f"get_agents Success")
            return agents
        except Exception as e:
            logger.warning(f"get_agents Error has occurred: {e}")
            return "error"
    agent.register_action(
        action_name="get_agents", 
        function=get_agents,
        description="Get the list of Agents and Actions", 
        arguments_schema="none",
        output_schema={
            "description": "List of agents",
            "type": "array",
            "items": {
                "description": "An echo agent instance",
                "type": "object"
            }
        }
    )

    def get_action(arguments):
        """ Slash command to get agent data"""
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            agent = arguments["agent"]
            action = arguments["action"]
            logger.info(f"Getting Action {agent}, {action}")
            action_info = echo.get_action(agent_name=agent, action_name=action)
            logger.info(f"get_action Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return action_info
        except Exception as e:
            logger.warning(f"get_action Error has occurred: {e}")
            return "error"
    agent.register_action(
        action_name="get_action", 
        function=get_action,
        description="Get an actions with argument and output metadata", 
        arguments_schema={
            "type": "object",
            "properties": {
                "agent": {
                    "description": "The agent name",
                    "type": "string"
                },
                "action": {
                    "description": "The action name",
                    "type": "string"
                }
            }
        },
        output_schema={
            "description": "An action",
            "type": "object",
            "properties": {
                "name": {
                    "description": "Action Name",
                    "type": "string"
                },
                "description":{
                    "description": "Action Description",
                    "type": "string"
                },
                "arguments_schema": {
                    "description": "Simplified Schema for arguments",
                    "type": "object"
                },
                "output_schema": {
                    "description": "Simplified schema for output",
                    "type": "object"
                }
            }
        }
    )

    logger.info("Registered echo agent action handlers.")
    return agent