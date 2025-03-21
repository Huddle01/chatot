import os
import asyncio
import logging
from dotenv import load_dotenv
from huddle import Huddle01Manager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("HUDDLE01_API_KEY")
PROJECT_ID = os.getenv("HUDDLE01_PROJECT_ID")
ROOM_ID = "vpw-cgxn-toa" 

async def main():
    """Main function to demonstrate Huddle01Manager usage"""
    
    # Validate environment variables
    if not API_KEY or not PROJECT_ID:
        logger.error("Missing required environment variables. Please set HUDDLE01_API_KEY and HUDDLE01_PROJECT_ID")
        return
    
    huddle_manager = Huddle01Manager(project_id=PROJECT_ID, api_key=API_KEY)
    
    try:
        logger.info(f"Attempting to join room: {ROOM_ID}")
        await huddle_manager.join_room(room_id=ROOM_ID)
        logger.info(f"Successfully joined room: {ROOM_ID}")
        
        
        # Keep the connection alive for some time
        await asyncio.sleep(30) 
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
