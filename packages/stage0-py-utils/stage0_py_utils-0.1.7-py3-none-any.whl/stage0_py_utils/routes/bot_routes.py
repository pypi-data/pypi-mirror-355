from stage0_py_utils.services.bot_services import BotServices
from stage0_py_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from stage0_py_utils.flask_utils.token import create_flask_token

import logging
logger = logging.getLogger(__name__)

from flask import Blueprint, Response, jsonify, request

# Define the Blueprint for bot routes
def create_bot_routes():
    bot_routes = Blueprint('bot_routes', __name__)

    # GET /api/bots - Return a list of bots that match query
    @bot_routes.route('', methods=['GET'])
    def get_bots():
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            query = request.args.get('query') or ""
            bots = BotServices.get_bots(query, token)
            logger.info(f"get_bots Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(bots), 200
        except Exception as e:
            logger.warning(f"get_bots Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # GET /api/bot/{id} - Return a specific bot
    @bot_routes.route('/<string:id>', methods=['GET'])
    def get_bot(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            bot = BotServices.get_bot(id, token)
            logger.info(f"get_bot Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(bot), 200
        except Exception as e:
            logger.warning(f"get_bot Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500

    # PATCH /api/bot/{id} - Update a bot
    @bot_routes.route('/<string:id>', methods=['PATCH'])
    def update_bot(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            patch_data = request.get_json()
            bot = BotServices.update_bot(id, token, breadcrumb, patch_data)
            logger.info(f"update_bot Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(bot), 200
        except Exception as e:
            logger.warning(f"update_bot processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # GET /api/bot/{id}/channels - Get Active Channels
    @bot_routes.route('/<string:id>/channels', methods=['GET'])
    def get_channels(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            channels = BotServices.get_channels(id, breadcrumb)
            logger.info(f"get_channels Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(channels), 200
        except Exception as e:
            logger.warning(f"get_channels processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500

    # POST /api/bot/{id}/channel/{channel_id} - Add a channel
    @bot_routes.route('/<string:id>/channel/<string:channel_id>', methods=['POST'])
    def add_channel(id, channel_id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            channels = BotServices.add_channel(id, token, breadcrumb, channel_id)
            logger.info(f"add_channel Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(channels), 200
        except Exception as e:
            logger.warning(f"add_channel processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500

    # DELETE /api/bot/{id}/channel/{channel_id} - Remove a channel
    @bot_routes.route('/<string:id>/channel/<string:channel_id>', methods=['DELETE'])
    def remove_channel(id, channel_id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            channels = BotServices.remove_channel(id, token, breadcrumb, channel_id)
            logger.info(f"remove_channel Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(channels), 200
        except Exception as e:
            logger.warning(f"remove_channel processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500

    logger.info("Bot Flask Routes Registered")
    return bot_routes