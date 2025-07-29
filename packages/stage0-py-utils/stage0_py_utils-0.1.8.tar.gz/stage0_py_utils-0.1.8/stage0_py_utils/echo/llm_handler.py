import re
import json
import datetime

from bson import ObjectId
from stage0_py_utils.echo.message import Message

import logging
logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)

class LLMHandler:
    """_summary_
    LLM handler implements the inner/outer chat discussions used by
    the Chat Engine. It persists the conversation using the 
    /conversation/add_message Agent Action
    """
    def __init__(self, echo_bot_name="Echo", handle_command_function=None, llm_client=None):
        """
        Initializes LLMHandler with an Echo agent framework and an LLM client.

        :param handle_command_function: Echo handle command function
        :param llm_client: Instance of LLMClient for LLM chat processing. (ollama_llm_client)
        """
        self.llm = llm_client
        self.echo_bot_name = echo_bot_name
        self.handle_command = handle_command_function
        self.agent_command_pattern = re.compile(r"^/(\S+)/(\S+)(?:/(.*))?$")

    def handle_message(self, channel=None, text=None, user="unknown", role=Message.USER_ROLE, dialog=Message.GROUP_DIALOG ):
        """
        Processes an incoming message, using it to update the conversation, 
        and generate a reply. If the reply is on the "internal" dialog it will 
        process the message by invoking the requested agent/action. 

        :param user: The username of the sender.
        :param channel: The Discord channel where the message originated.
        :param message: The message content.
        :param dialog: The "internal" or "external" dialog this message will be posted to, defaults to external
        :return: The response to be written to the chat-channel. 
        """
        
        # Step 1: Add the user message to the conversation
        logger.debug(f"Posting Message {text}")
        message = Message(encoded_text=text, role=role, user=user, dialog=dialog)
        messages = self.post_message(channel=channel, message=message)

        # Step 2: Check if this is an agent call using regex
        match = self.agent_command_pattern.match(text)
        if match:
            agent = match.group(1)
            agent_reply = self.handle_command(text)
            agent_reply_string = self.stringify(agent_reply)
            message = Message(user=agent, role=Message.USER_ROLE, dialog=dialog, text=agent_reply_string)
            messages = self.post_message(channel=channel, message=message)
            # If this was a direct user to agent call, return the reply to the group.
            if dialog == Message.GROUP_DIALOG: return agent_reply_string

        # Step 3: Call the LLM with updated conversation history
        logger.debug(f"LLM Chat Prompt: {messages[len(messages)-1]["content"]}")
        llm_reply = self.llm.chat(messages=messages)
        logger.debug(f"LLM Reply Object: {llm_reply}")
        chat_reply = Message(llm_message=llm_reply["message"], user=self.echo_bot_name)
        logger.debug(f"LLM Chat Reply: {chat_reply.role}-{chat_reply.text[:49].strip()}...")

        # Step 4: Process LLM response recursively if it's an tool message
        if chat_reply.dialog == Message.TOOLS_DIALOG:
            logger.debug(f"Process LLM response recursively {chat_reply.text}")
            return self.handle_message(channel=channel, user=chat_reply.user, role=chat_reply.role, text=chat_reply.text, dialog=chat_reply.dialog)

        # Step 6: Add LLM response to conversation and return it
        logger.debug(f"Posting LLM response message to chat: {chat_reply.text}")
        self.post_message(channel=channel, message=chat_reply)
        return chat_reply.text

    def post_message(self, channel=None, message=None):
        """
        Helper function to add a message to the conversation
        Uses the /conversation/add_message agent action
        
        :param channel: The channel_id for the conversation
        :param message: a Echo Message object
        :return: The full conversation (list of messages)
        """
        arguments = json.dumps({"channel_id": channel, "message":message.as_llm_message()}, separators=(',', ':'))
        command = f"/conversation/add_message/{arguments}"
        logger.debug(f"Sending the command: {command}")
        conversation = self.handle_command(command)
        return conversation if isinstance(conversation, list) else []

    def stringify(self, obj):
        """Recursively convert ObjectId and datetime values to strings, then minify JSON."""
        def stringify_mongo_objects(obj):
            if isinstance(obj, dict):  
                return {k: stringify_mongo_objects(v) for k, v in obj.items()}
            elif isinstance(obj, list):  
                return [stringify_mongo_objects(i) for i in obj]
            elif isinstance(obj, (ObjectId, datetime.datetime)):  
                return str(obj)  
            return obj  # Return unchanged if it's another type

        return json.dumps(stringify_mongo_objects(obj), separators=(',', ':'))  