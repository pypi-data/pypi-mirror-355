import csv
from io import StringIO
from stage0_py_utils.mongo_utils.mongo_io import MongoIO
from stage0_py_utils.config.config import Config
from stage0_py_utils.echo.message import Message
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationServices:
    CYAN = "\033[36m "
    BLUE = "\033[94m"
    RESET = "\033[0m"        

    @staticmethod 
    def _check_user_access(token):
        """Role Based Access Control logic"""
        return # No RBAC yet

    @staticmethod
    def get_conversations(token=None):
        """
        Get a list of the latest segment of all active conversations

        Args:
            token (token): Access Token from the requesting agent

        Returns:
            list: List of currently active conversations. (_id, name)
        """
        ConversationServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        match = {"$and": [
            {"version": config.LATEST_VERSION},
            {"status": config.ACTIVE_STATUS}
        ]}
        project = {"_id":1, "channel_id":1}
        conversations = mongo.get_documents(config.CONVERSATION_COLLECTION_NAME, match, project)
        return conversations

    @staticmethod
    def get_all_conversations_by_name(query=None, token=None):
        """
        Get a list of conversation _id and name (channel_id)

        Args:
            query (str): Regex of channel_id values to return
            token (token): Access Token from the requesting agent

        Returns:
            list: List of { _id: "XX", name: "XX"} values
                where name matches the regex provided in the query parameter
                including inactive and archived documents   
        """
        ConversationServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        match = {"channel_id": {"$regex": query}} if query else None
        project = {"_id":1, "channel_id":1}
        conversations = mongo.get_documents(config.CONVERSATION_COLLECTION_NAME, match, project)
        return conversations

    @staticmethod
    def get_conversation(channel_id=None, token=None, breadcrumb=None):
        """Get the specified conversation"""
        ConversationServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        match = {"$and": [
            {"channel_id": channel_id},
            {"version": config.LATEST_VERSION},
            {"status": config.ACTIVE_STATUS}
        ]}
        conversations = mongo.get_documents(collection_name=config.CONVERSATION_COLLECTION_NAME, match=match)
        if len(conversations) == 0:
            data = {}
            data["channel_id"] = channel_id
            data["status"] = config.ACTIVE_STATUS
            data["version"] = config.LATEST_VERSION
            data["last_saved"] = breadcrumb
            data["messages"] = []
            new_id = mongo.create_document(collection_name=config.CONVERSATION_COLLECTION_NAME, document=data)
            conversation = mongo.get_document(collection_name=config.CONVERSATION_COLLECTION_NAME, document_id=new_id)
            return conversation
        else:
            return conversations[0]
        
    @staticmethod
    def update_conversation(channel_id=None, data=None, token=None, breadcrumb=None):
        """Update the latest version of the specified conversation"""
        ConversationServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        match = {"$and": [
            {"channel_id": channel_id},
            {"version": config.LATEST_VERSION},
            {"status": config.ACTIVE_STATUS}
        ]}
        data["last_saved"] = breadcrumb
        conversation = mongo.update_document(config.CONVERSATION_COLLECTION_NAME, match=match, set_data=data)
        return conversation
    
    @staticmethod
    def add_message(channel_id=None, message=None, token=None, breadcrumb=None):
        """Add a message to the conversation and generate a reply"""
        ConversationServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        
        # Fetch the existing conversation, create it if needed
        conversation = ConversationServices.get_conversation(channel_id=channel_id, token=token, breadcrumb=breadcrumb)
        if len(conversation["messages"]) > 1000: #TODO: Add config.MAX_MESSAGES
            conversation = ConversationServices.reset_conversation(channel_id=channel_id, token=token, breadcrumb=breadcrumb)
        
        # Update Conversation - push message onto messages
        match = {"$and": [
            {"channel_id": channel_id},
            {"version": config.LATEST_VERSION},
            {"status": config.ACTIVE_STATUS}
        ]}
        set_data = {"last_saved": breadcrumb}
        push_data = {"messages": message}
        reply = mongo.update_document(config.CONVERSATION_COLLECTION_NAME, match=match, set_data=set_data, push_data=push_data)
        messages = reply["messages"]
        
        ConversationServices.colorful_log(["Message added to:", channel_id, " with role:", message["role"], " content:", message["content"][:60]])
        return messages

    @staticmethod
    def reset_conversation(channel_id=None, token=None, breadcrumb=None):
        """Move the active conversation to complete and set the version string"""
        ConversationServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        reply = {}
        
        match = {"$and": [
            {"channel_id": channel_id},
            {"version": config.LATEST_VERSION},
            {"status": config.ACTIVE_STATUS}
        ]}
        set_data = {
            "version": datetime.now().strftime("%Y-%m-%d%H:%M:%S"),
            "status": config.COMPLETED_STATUS,
            "last_saved": breadcrumb
        }
        reply = mongo.update_document(config.CONVERSATION_COLLECTION_NAME, match=match, set_data=set_data) or "Nothing to reset"

        ConversationServices.colorful_log(["Conversation:", channel_id, " has been reset"])
        return reply

    @staticmethod
    def load_named_conversation(channel_id=None, named_conversation=None, token=None, breadcrumb=None):
        """Copy the messages from the named conversation to the channels conversation."""
        ConversationServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        
        # Get the named conversation
        match = {"$and": [
            {"channel_id": named_conversation},
            {"version": config.LATEST_VERSION},
            {"status": config.ACTIVE_STATUS}
        ]}
        source_conversation_list = mongo.get_documents(config.CONVERSATION_COLLECTION_NAME, match=match)
        if not source_conversation_list or len(source_conversation_list) == 0:
            raise Exception(f"Named Conversation {named_conversation} was not found")
        if len(source_conversation_list) > 1:
            logger.warning(f"Non-Unique Named Conversation! {len(source_conversation_list)} conversations named {named_conversation} were found")
        source_conversation = source_conversation_list[0]
        
        # Add the Messages from the source to the Channel Conversation
        # Make sure the target conversation exists first. 
        target_conversation = ConversationServices.get_conversation(channel_id=channel_id, token=token, breadcrumb=breadcrumb)
        match = {"$and": [
            {"channel_id": channel_id},
            {"version": config.LATEST_VERSION},
            {"status": config.ACTIVE_STATUS}
        ]}
        set_data = {
            "last_saved": breadcrumb
        }
        push_data = {"messages": {"$each": source_conversation["messages"]}}
        target_conversation = mongo.update_document(config.CONVERSATION_COLLECTION_NAME, match=match, set_data=set_data, push_data=push_data)

        ConversationServices.colorful_log(["Conversation:", named_conversation, " has loaded ", str(len(source_conversation["messages"])), " messages into ", channel_id])
        return target_conversation

    @staticmethod
    def load_given_conversation(channel_id=None, csv_data=None, token=None, breadcrumb=None):
        """Copy the messages from the csv_data to the channels conversation."""
        ConversationServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        
        # Parse the CSV data and load messages
        reader = csv.DictReader(StringIO(csv_data), quotechar='"', skipinitialspace=True)
        messages = [
            Message(
                role=row["role"],
                user=row["from"],
                dialog=row["to"],
                text=row["text"]
            ).as_llm_message()
            for row in reader
        ]        
        
        # Make sure the target conversation exists first. 
        target_conversation = ConversationServices.get_conversation(channel_id=channel_id, token=token, breadcrumb=breadcrumb)
        
        # Update the database
        match = {"$and": [
            {"channel_id": channel_id},
            {"version": config.LATEST_VERSION},
            {"status": config.ACTIVE_STATUS}
        ]}
        set_data = {
            "last_saved": breadcrumb
        }
        push_data = {"messages": {"$each": messages}}
        target_conversation = mongo.update_document(config.CONVERSATION_COLLECTION_NAME, match=match, set_data=set_data, push_data=push_data)

        ConversationServices.colorful_log(["Conversation:", channel_id, " has loaded ", str(len(messages)), " messages from the provided csv data"])
        return target_conversation

    @staticmethod
    def colorful_log(strings=None):
        """Logs a list of strings with alternating BLUE and CYAN colors."""
        colors = [ConversationServices.BLUE, ConversationServices.CYAN]
        colored_message = "".join(f"{colors[i % 2]}{msg}" for i, msg in enumerate(strings)) + ConversationServices.RESET
        logger.info(colored_message)
        pass

