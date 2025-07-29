import logging
from stage0_py_utils.config.config import Config
from stage0_py_utils.echo.agent import Agent
from stage0_py_utils.echo_utils.token import create_echo_token
from stage0_py_utils.echo_utils.breadcrumb import create_echo_breadcrumb

logger = logging.getLogger(__name__)

def create_config_agent(agent_name):
    """ Registers event handlers and commands for the Config Agent. """
    agent = Agent(agent_name)
    
    def get_config(arguments):
        """ Slash command to get config data"""
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            config = Config.get_instance()
            logger.info(f"remove_channel Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")            
            return config.to_dict(token=token)
        except Exception as e:
            logger.warning(f"get_config Error has occurred: {e}")
            return "error"
    agent.register_action(
        action_name="get_config", 
        function=get_config,
        description="Get the Bot Configuration information", 
        arguments_schema="none",
        output_schema={
            "type": "object",
            "description": "",
            "properties": {
                "config_items": {
                    "description": "List of Configuration Items and non-secret values",
                "type": "array"
                },
                "versions": {
                    "description": "List of database collection versions",
                    "type": "array"
                },
                "enumerators": {
                    "description": "Collection of Enumerators",
                    "type": "object"
                },
                "token": {
                    "description": "Data extracted from the token used when requesting configuration data",
                    "type": "object"
                }
            }
        }
    )

    logger.info("Registered config agent action handlers.")
    return agent