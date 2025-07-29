from typing import Any, Callable
import logging
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name: str, description=""):
        """Initialize an agent with a name and an empty action registry."""
        self.name = name
        self.description = description
        self.actions = {}

    def register_action(self, 
            action_name: str, 
            function: Callable[[Any], Any], 
            description: str, 
            arguments_schema: dict, 
            output_schema: dict):
        """Registers an action with required metadata and ensures validity."""
        if not all([action_name, function, description, arguments_schema, output_schema]):
            raise ValueError("Missing required attributes for action registration")

        self.actions[action_name] = {
            "function": function,
            "description": description,
            "arguments_schema": arguments_schema,
            "output_schema": output_schema
        }

    def get_actions(self) -> list:
        """Returns a list of registered action names."""
        return list(self.actions.keys())

    def invoke_action(self, action_name: str, arguments: dict):
        """
        Executes a registered action asynchronously.
        - Returns the result if successful.
        - Returns an error message if the action is not found.
        """
        if action_name not in self.actions:
            logger.debug(f"Action {action_name} not found")
            return f"Error: Action '{action_name}' not found"

        action = self.actions[action_name]["function"]
        return action(arguments)
    
    # def as_dict(self):
    #     """Returns a dictionary representation of the agent and its actions."""
    #     actions = []
    #     for action_name, action_data in self.actions.items():
    #         action_dict = {
    #             "name": action_name,
    #             "description": action_data["description"],
    #             "arguments_schema": action_data["arguments_schema"],
    #             "output_schema": action_data["output_schema"]
    #         }
    #         actions.append(action_dict)

    #     return {
    #         "name": self.name,
    #         "actions": actions
    #     }