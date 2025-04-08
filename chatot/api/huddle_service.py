import asyncio
import logging
import threading
from chatot.huddle import Huddle01Manager

logger = logging.getLogger(__name__)

async def join_huddle_room(project_id, api_key, room_id, loop):
    """
    Join a Huddle01 room and return the manager and success status.

    Returns:
        tuple: (huddle_manager, success_flag, error_message)
    """
    try:
        huddle_manager = Huddle01Manager(project_id=project_id, api_key=api_key, loop=loop)
        try:
            result = await huddle_manager.join_room(room_id=room_id)
        except Exception as e:
            await huddle_manager.leave_room()
            return None, False, f"Failed to join room: {str(e)}"

        if not result:
            logger.error(f"Failed to join room {room_id}")
            return None, False, f"Failed to join room {room_id}"

        logger.info(f"Successfully joined room {room_id}")
        return huddle_manager, True, "Room joined successfully"
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        return None, False, str(e)


def setup_room_manager_thread(room_id, project_id, api_key):
    """
    Sets up a thread to manage a Huddle01 room session.
    """
    result_container = {}

    def run_room_manager(room_id, result_dict):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        huddle_manager = None

        join_result = loop.run_until_complete(join_huddle_room(project_id, api_key, room_id, loop))
        huddle_manager, success, message = join_result

        if not success:
            result_dict['status_code'] = 500
            result_dict['message'] = message
            loop.close()
            return

        result_dict['status_code'] = 200
        result_dict['message'] = message
        result_dict['manager_thread'] = threading.current_thread()
        result_dict['loop'] = loop
        result_dict['manager'] = huddle_manager

        async def leave_room_async():
            try:
                if huddle_manager:
                    await huddle_manager.leave_room()
                    logger.info(f"Room {room_id} left successfully")
                    result_dict['leave_status'] = 200
                    result_dict['leave_message'] = "Room left successfully"
            except Exception as e:
                logger.error(f"Error leaving room: {e}")
                result_dict['leave_status'] = 500
                result_dict['leave_message'] = str(e)
            finally:
                loop.stop()

        def stop_callback():
            asyncio.run_coroutine_threadsafe(leave_room_async(), loop)

        if huddle_manager:
            huddle_manager.once("completed", leave_room_async)

        result_dict['stop_callback'] = stop_callback

        try:
            loop.run_forever()
        finally:
            loop.close()
            logger.info(f"Event loop for room {room_id} closed")

    thread = threading.Thread(target=run_room_manager, args=(room_id, result_container))
    thread.daemon = True
    thread.start()

    thread.join(timeout=5.0)

    return result_container
