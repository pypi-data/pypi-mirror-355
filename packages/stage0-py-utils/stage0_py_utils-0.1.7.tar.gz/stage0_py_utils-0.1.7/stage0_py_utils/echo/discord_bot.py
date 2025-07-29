import discord
import json
import logging
from stage0_py_utils.echo.message import Message

logger = logging.getLogger(__name__)

class DiscordBot(discord.Client):
    """_summary_
    This class handles interactions with Discord, and implements the on_message
    event handler. It maintains the list of active channels that the bot is participating in 
    and implements the channel join/leave logic. It uses the LLM handle_message_function 
    to process any messages that are not join/leave messages.
    """
    def __init__(self, handle_command_function=None, handle_message_function=None,  bot_id=None, **kwargs):
        """
        Initializes the Discord bot 

        :param handle_command_function: Function used to execute an agent action.
        :param handle_message_function: Function used to ask the LLM to handle a message
        :param bot_id: Unique Identifier of the Bot Record in the stage0 system.
        """
        intents = kwargs.pop("intents", discord.Intents.default())
        intents.messages = True
        intents.message_content = True
        intents.guilds = True
        intents.dm_messages = True  

        super().__init__(intents=intents, **kwargs)
        self.handle_command = handle_command_function
        self.handle_message = handle_message_function
        self.bot_id = bot_id
        self.active_channels = []  

    async def on_ready(self):
        """
        Triggered when the bot successfully connects, trigger the loading of 
        active channels from the /bot/get_channels action
        """
        logger.info(f"Logged in as {self.user}")
        try:
            arguments = json.dumps(self.bot_id, separators=(',', ':'))
            self.active_channels = self.handle_command(f"/bot/get_channels/{arguments}")
            logger.info(f"Initialized active channels: {self.active_channels}")
        except Exception as e:
            logger.warning(f"Failed to initialize active channels: {e}")

    async def on_message(self, message):
        """
        Processes incoming messages from Discord. 
        Handles all join/leave logic
        Passes messages to the LLM handle_message_function
        """
        logger.debug(f"Got a message!")
        if message.author == self.user:
            return  # Ignore self-messages

        # Initialize Message Values
        user_id = message.author.id
        username = message.author.name
        channel = message.channel.id if message.guild else f"DM-{user_id}"
        channel = str(channel) if channel is not None else ""
        content = message.content
        if not content: logger.warning(f"Content is None")
        logger.debug(f"Processing message for: {username}-{user_id}: channel: {channel} content: {content}")

        response = ""
        try:
            # Always Join DM channels if they are not already active
            if message.guild is None and channel not in self.active_channels:
                logger.debug(f"Joining DM Channel {channel}")
                response = self.update_active_channels(action="add_channel", channel=channel)
                await message.channel.send(response)                
                
            # Leave Channels when requested
            if self.user in message.mentions and "leave" in content.lower():
                logger.debug(f"Leaving Channel {channel}")
                response = self.update_active_channels(action="remove_channel", channel=channel)
                
            # Reset the Channels conversation when requested
            elif self.user in message.mentions and "reset" in content.lower():
                logger.debug(f"Resetting Channel Conversation {channel}")
                response = self.reset_channel_conversation(channel=channel)
                
            # Load a named conversation into this Channels conversation when requested
            elif self.user in message.mentions and "load" in content.lower():
                name = content.split()[-1] 
                logger.debug(f"Loading Conversation {name} Conversation {channel}")
                response = self.load_named_channel(channel=channel, named_conversation=name)
                
            # Join Channels when requested
            elif self.user in message.mentions and "join" in content.lower():
                logger.debug(f"Joining Channel {channel}")
                response = self.update_active_channels(action="add_channel", channel=channel)

            # Process Message if from an active channel            
            elif channel in self.active_channels:
                logger.debug(f"Getting LLM Response in {channel}")
                response = self.handle_message(channel=channel, user=username, role=Message.USER_ROLE, dialog=Message.GROUP_DIALOG, text=content)
                
            # Send the reply message
            logger.debug(f"Sending response {response}.")
            response = response.strip()
            if len(response) > 2000:
                response = f"{response[:1950]}-TRUNCATED"
                
            if len(response) > 0:
                await message.channel.send(response)

            logger.debug(f"on_message processing complete {content}.")
            return

        except Exception as e:
            logger.warning(f"Echo bot On-Message Error: {e}, username: {username} user_id: {user_id}: channel: {channel} content: {content}")
            raise e

    def update_active_channels(self, action=None, channel=None):
        """
        Updates the list of active channels using the bot_agent actions.
        """
        try:
            arguments = json.dumps({"bot_id": self.bot_id,"channel_id": channel}, separators=(',', ':'))
            channels =  self.handle_command(f"/bot/{action}/{arguments}")
            if isinstance(channels, list):
                self.active_channels = channels
                return f"✅ Channel: {channel} {'added to' if action == 'add_channel' else 'removed from'} active channels list."
            else:
                logger.warning(f"bot/{action}/{arguments} did not return a list")
                return f"❎ Something went wrong, Try again later"
        except Exception as e:
            raise Exception(f"Failed to update active channels: {e}")

    def reset_channel_conversation(self, channel=None):
        """
        Calls the channel reset agent action
        """
        try:
            conversation =  self.handle_command(f'/conversation/reset_conversation/"{channel}"')
            if isinstance(conversation, dict):
                return f"✅ The conversation in channel: {channel} has been reset."
            else:
                logger.warning(f'/conversation/reset_conversation/"{channel}" caused an error')
                return f"❎ Something went wrong, Try again later"
        except Exception as e:
            raise Exception(f"Failed to reset a conversation: {e}")

    def load_named_channel(self, channel=None, named_conversation=None):
        """
        Calls the load_personality agent action
        """
        try:
            arguments = json.dumps({
                "channel_id": channel,
                "named_conversation": named_conversation
            }, separators=(',', ':'))
            conversation =  self.handle_command(f'/conversation/load_personality/{arguments}')
            if isinstance(conversation, dict):
                return f"✅ The {named_conversation} personality has been loaded into this conversation. ({channel})"
            else:
                logger.warning(f'/conversation/load_personality/"{arguments}" caused an error')
                return f"❎ Something went wrong, Try again later"
        except Exception as e:
            raise Exception(f"Failed to reset a conversation: {e}")
