from stage0_py_utils.echo.message import Message
from stage0_py_utils.services.conversation_services import ConversationServices
from stage0_py_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from stage0_py_utils.flask_utils.token import create_flask_token

import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, Response, jsonify, request

# Define the Blueprint for conversation routes
def create_conversation_routes():
    conversation_routes = Blueprint('conversation_routes', __name__)

    # GET /api/conversations - Return a list of latest active conversations
    @conversation_routes.route('', methods=['GET'])
    def get_conversations():
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            conversations = ConversationServices.get_conversations(token=token)
            logger.info(f"get_conversations Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(conversations), 200
        except Exception as e:
            logger.warning(f"get_conversations Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # GET /api/conversation/channel_id - Return a specific conversation
    @conversation_routes.route('/<string:channel_id>', methods=['GET'])
    def get_conversation(channel_id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            conversation = ConversationServices.get_conversation(channel_id=channel_id, token=token, breadcrumb=breadcrumb)
            logger.info(f"get_conversation Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(conversation), 200
        except Exception as e:
            logger.warning(f"get_conversation Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500

    # PATCH /api/conversation/{channel_id} - Update a conversation
    @conversation_routes.route('/<string:channel_id>', methods=['PATCH'])
    def update_conversation(channel_id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            data = request.get_json()
            conversation = ConversationServices.update_conversation(channel_id=channel_id, data=data, token=token, breadcrumb=breadcrumb)
            logger.info(f"update_conversation Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(conversation), 200
        except Exception as e:
            logger.warning(f"update_conversation processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # POST /api/conversation/{channel_id}/message - Add a message to a conversation
    @conversation_routes.route('/<string:channel_id>/message', methods=['POST'])
    def add_message(channel_id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            message = Message(llm_message=request.get_json(), user=token["user_id"])
            messages = ConversationServices.add_message(channel_id=channel_id, message=message.as_llm_message(), token=token, breadcrumb=breadcrumb)
            logger.info(f"add_message Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(messages), 200
        except Exception as e:
            logger.warning(f"add_message processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # POST /api/conversation/{channel_id}/reset - Reset the currently active conversation 
    @conversation_routes.route('/<string:channel_id>/reset', methods=['POST'])
    def reset_conversation(channel_id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            messages = ConversationServices.reset_conversation(channel_id=channel_id, token=token, breadcrumb=breadcrumb)
            logger.info(f"reset_conversation Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(messages), 200
        except Exception as e:
            logger.warning(f"reset_conversation processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # POST /api/conversation/{channel_id}/load/{named_conversation} - Load all the messages from the named conversation to the channel conversation
    @conversation_routes.route('/<string:channel_id>/load/<string:named_conversation>', methods=['POST'])
    def load_conversation(channel_id, named_conversation):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            messages = ConversationServices.load_named_conversation(
                channel_id=channel_id, 
                named_conversation=named_conversation, 
                token=token, breadcrumb=breadcrumb)
            logger.info(f"load_conversation Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(messages), 200
        except Exception as e:
            logger.warning(f"load_conversation processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500

    # POST /api/conversation/{channel_id}/initialize - Load all the messages from a csv file
    @conversation_routes.route('/<string:channel_id>/initialize', methods=['POST'])
    def initialize_conversation(channel_id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            data = request.get_data(as_text=True)
            ConversationServices.reset_conversation(
                channel_id=channel_id, 
                token=token, breadcrumb=breadcrumb)
            messages = ConversationServices.load_given_conversation(
                channel_id=channel_id, 
                csv_data=data, 
                token=token, breadcrumb=breadcrumb)
            logger.info(f"initialize_conversation Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(messages), 200
        except Exception as e:
            logger.warning(f"initialize_conversation processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500

    logger.warning(f"TypeOf initialize_conversation {type(initialize_conversation)}")
    return conversation_routes