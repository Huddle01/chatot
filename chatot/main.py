import os
import logging
from dotenv import load_dotenv
from chatot.api import apiHandler
from chatot.utils.webhook_sender import WebhookSender

# Configure logging
logging.basicConfig(
    level=logging.NOTSET, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("HUDDLE01_API_KEY")
PROJECT_ID = os.getenv("HUDDLE01_PROJECT_ID")
WEBHOOK_URL= os.getenv("WEBHOOK_URL")

if not API_KEY or not PROJECT_ID:
    logger.error(
        "Missing required environment variables. Please set HUDDLE01_API_KEY, HUDDLE01_PROJECT_ID"
    )
    raise Exception("Invalid Environment Variables")


if __name__ == "__main__":
    # Run the async main function
    logger.setLevel(logging.DEBUG)

    if WEBHOOK_URL:
        logger.info("INITIALISING WEBHOOK ENDPOINT")
        WebhookSender(endpoint_url=WEBHOOK_URL)
    logger.info("Starting API Server")
    apiHandler.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
