import os
import asyncio
import logging
from dotenv import load_dotenv
from chatot.huddle import Huddle01Manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("HUDDLE01_API_KEY")
PROJECT_ID = os.getenv("HUDDLE01_PROJECT_ID")
ROOM_ID = os.getenv("ROOM_ID")


async def main():
    """Main function to demonstrate Huddle01Manager usage"""

    # Validate environment variables
    if not API_KEY or not PROJECT_ID or not ROOM_ID:
        logger.error(
            "Missing required environment variables. Please set HUDDLE01_API_KEY, HUDDLE01_PROJECT_ID and ROOM_ID"
        )
        return

    huddle_manager = Huddle01Manager(project_id=PROJECT_ID, api_key=API_KEY)

    try:
        await huddle_manager.join_room(room_id=ROOM_ID)

        await asyncio.sleep(10)
        await huddle_manager.leave_room()

    except Exception as e:
        logger.error(f"Error during room operations: {e}")
    finally:
        # Make sure to always leave the room properly
        if huddle_manager.room:
            await huddle_manager.leave_room()
            logger.info("Room cleanup completed")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
