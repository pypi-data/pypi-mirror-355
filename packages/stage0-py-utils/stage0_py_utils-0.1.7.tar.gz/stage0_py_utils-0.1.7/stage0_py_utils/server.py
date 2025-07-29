"""_summary_
This is a sample server that uses Flask and Echo to serve up endpoints and agents related to Bots, Conversations, and Agents

The Bot document keeps a list of "active channels" that the bot is listening
The Conversation document contains a list of Messages for a channel
The Echo agent describes the agents and actions that are registered to the Echo framework. 
"""
import sys
import signal
import threading
from werkzeug.serving import make_server

# Initialize Singletons
from stage0_py_utils import Config, MongoIO
config = Config.get_instance()
mongo = MongoIO.get_instance()

# Initialize Logging
import logging
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

logger.info(f"============= Starting Server Initialization ===============")

# Initialize Echo Discord Bot - this will register the default Bot/Conversation/Echo Agents
from stage0_py_utils import Echo
from stage0_py_utils import OllamaLLMClient
llm_client = OllamaLLMClient(base_url=config.OLLAMA_HOST, model=config.FRAN_MODEL_NAME)
echo = Echo("Fran", bot_id=config.FRAN_BOT_ID, model=config.FRAN_MODEL_NAME, client=llm_client)
# from echo.mock_llm_client import MockLLMClient
# echo = Echo("Fran", bot_id=config.FRAN_BOT_ID, model=config.FRAN_MODEL_NAME, client=MockLLMClient())

# Register Config Agents
from stage0_py_utils import create_config_agent
echo.register_agent(create_config_agent(agent_name="config"))

##################################
## - Add your agents here
##################################

logger.info(f"============= Agents Initialized ===============")

# Initialize Flask App
from flask import Flask
from stage0_py_utils import MongoJSONEncoder
from prometheus_flask_exporter import PrometheusMetrics
app = Flask(__name__)
app.json = MongoJSONEncoder(app)

# Apply Prometheus monitoring middleware
metrics = PrometheusMetrics(app, path='/api/health/')
metrics.info('app_info', 'Application info', version=config.BUILT_AT)

# Register Echo framework flask routes
echo.register_default_routes(app=app)

# Register Config Routes
from stage0_py_utils import create_config_routes
app.register_blueprint(create_config_routes(), url_prefix='/api/config')

##################################
##### Add your Routes here
##################################

logger.info(f"============= Routes Registered ===============")

##################################
##### Code below here uses the FRAN port and token config values
#####   Update to use your apps values.

# Flask server run's in it's own thread
server = make_server("0.0.0.0", config.FRAN_API_PORT, app)
flask_thread = threading.Thread(target=server.serve_forever)

# Define a signal handler for SIGTERM and SIGINT
def handle_exit(signum, frame):
    logger.info(f"Received signal {signum}. Initiating shutdown...")

    # Shutdown Flask gracefully
    if flask_thread.is_alive():
        logger.info("Stopping Flask server...")
        server.shutdown()
        flask_thread.join()

    # Disconnect from MongoDB
    logger.info("Closing MongoDB connection.")
    mongo.disconnect()

    # Close the Discord bot
    logger.info("Closing Discord connection.")
    echo.close(timeout=0.1) # TODO Add DISCORD_TIMEOUT config value with this default value

    logger.info("Shutdown complete.")
    sys.exit(0)  

# Register the signal handler
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# Start the bot and expose the app object for Gunicorn
if __name__ == "__main__":
    flask_thread.start()
    logger.info("Flask server started.")

    # Run Discord bot in the main thread
    echo.run(token=config.DISCORD_FRAN_TOKEN)
    