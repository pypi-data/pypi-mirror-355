import logging
from stage0_py_utils.echo.agent import Agent
from stage0_py_utils.services.conversation_services import ConversationServices
from stage0_py_utils.echo_utils.breadcrumb import create_echo_breadcrumb
from stage0_py_utils.echo_utils.token import create_echo_token

logger = logging.getLogger(__name__)

def create_conversation_agent(agent_name):
    """ Registers agent actions for Echo agent."""
    agent = Agent(agent_name)
    
    # Define reused schema's
    conversation_schema = {
        "description": "A conversation with a list of messages",
        "type": "object",
        "properties": {
            "_id": {
                "description": "The unique identifier for a conversation mongo document",
                "type": "identifier"
            },
            "status": {
                "description": "The unique identifier for a conversation mongo document",
                "type": "string",
                "enum": ["Active", "Archived"]
            },
            "channel_id": {
                "description": "The Discord channel_id this conversation is taking place in",
                "type": "string"
            },
            "version": {
                "description": "Either 'latest' or the date the conversation was archived",
                "type": "string"
            },
            "conversation": {
                "description": "Messages in the conversation",
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "last_saved": {
                "description": "Last Saved tracking breadcrumb",
                "type": "breadcrumb"
            }
        }
    }
    
    def get_conversations(arguments):
        """ """
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            conversations = ConversationServices.get_conversations(token=token)
            logger.info(f"get_conversations Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")            
            return conversations
        except Exception as e:
            logger.warning(f"Get conversations Error has occurred: {e}")
            return "error"
    agent.register_action(
        action_name="get_conversations",
        function=get_conversations,
        description="Return a list of active, latests, conversations", 
        arguments_schema={"none"},
        output_schema={
            "description": "List of name and id's of conversations that match the query",
            "type": "array",
            "items": {
                "type":"object",
                "properties": {
                    "_id": {
                        "description": "",
                        "type": "unique identifier",
                    },
                    "name": {
                        "description": "",
                        "type": "string",
                    },
                }
            }
        })

    def get_conversation(arguments):
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            conversation = ConversationServices.get_conversation(channel_id=arguments, token=token, breadcrumb=breadcrumb)
            logger.info(f"get_conversation Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")            
            return conversation
        except Exception as e:
            logger.warning(f"Get conversation Error has occurred: {e}")
            return "error"
    agent.register_action(
        action_name="get_conversation", 
        function=get_conversation,
        description="Get a conversation by ID", 
        arguments_schema={
            "description":"Channel Identifier",
            "type": "string", 
        },
        output_schema=conversation_schema
    )

    def update_conversation(arguments):
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            conversation = ConversationServices.update_conversation(
                channel_id=arguments["channel_id"], 
                conversation=arguments, 
                token=token, breadcrumb=breadcrumb)
            logger.info(f"update_conversation Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")            
            return conversation
        except Exception as e:
            logger.warning(f"Update conversation Error has occurred {e}")
            return "error"
    agent.register_action(
        action_name="update_conversation", 
        function=update_conversation,
        description="Update the specified conversation", 
        arguments_schema=conversation_schema,
        output_schema=conversation_schema
    )
        
    def add_message(arguments):
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            messages = ConversationServices.add_message(
                channel_id=arguments["channel_id"],
                message=arguments["message"], 
                token=token, breadcrumb=breadcrumb)
            logger.info(f"add_message Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")            
            return messages
        except Exception as e:
            logger.warning(f"Add Message Error has occurred {e}")
            return "error"
    agent.register_action(
        action_name="add_message", 
        function=add_message,
        description="Add a message to the specified conversation", 
        arguments_schema={
            "description":"A channel_id and the message to add",
            "type": "object", 
            "properties": {
                "channel_id": {
                    "description": "",
                    "type": "string"
                },
                "message": {
                    "description": "",
                    "type": "string"
                }                
            }
        },
        output_schema={    
            "description":"The new message in the conversational context",
            "type": "array", 
            "items": {
                "description": "A message in the conversation",
                "type": "string"
            }
        })
        
    def reset_conversation(arguments):
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            conversation = ConversationServices.reset_conversation(
                channel_id=arguments,
                token=token, breadcrumb=breadcrumb)
            logger.info(f"reset_conversation Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")            
            return conversation
        except Exception as e:
            logger.warning(f"Reset Conversation Error has occurred {e}")
            return "error"
    agent.register_action(
        action_name="reset_conversation", 
        function=reset_conversation,
        description="Reset (archive) the specified active Conversation", 
        arguments_schema={
            "description":"A channel_id",
            "type": "string" 
        },
       output_schema=conversation_schema
    )
        
    def load_personality(arguments):
        try:
            token = create_echo_token()
            breadcrumb = create_echo_breadcrumb(token)
            conversation = ConversationServices.load_named_conversation(
                channel_id=arguments["channel_id"],
                named_conversation=arguments["named_conversation"],
                token=token, breadcrumb=breadcrumb)
            logger.info(f"load_personality Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")            
            return conversation
        except Exception as e:
            logger.warning(f"load_personality Error has occurred {e}")
            return "error"
    agent.register_action(
        action_name="load_personality", 
        function=load_personality,
        description="Load the named conversation into the provided channel", 
        arguments_schema={
            "type": "object",
            "properties":{
                "channel_id": {
                    "description": "A channel_id",
                    "type": "string" 
                },
                "named_conversation": {
                    "description": "The named conversation to load",
                    "type": "string" 
                }
            }
        },
       output_schema=conversation_schema
    )

    logger.info("Registered conversation agent action handlers.")
    return agent