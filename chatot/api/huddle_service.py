import asyncio
import threading
from chatot.huddle import Huddle01Manager
import gc

# Configure logging
from chatot.log import base_logger
logger = base_logger.getChild(__name__)

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
            # Ensure cleanup in case of error
            try:
                await huddle_manager.leave_room()
            except Exception as leave_err:
                logger.error(f"Error while cleaning up after join failure: {leave_err}")
            return None, False, f"Failed to join room: {str(e)}"

        if not result:
            logger.error(f"Failed to join room {room_id}")
            await huddle_manager.leave_room()
            return None, False, f"Failed to join room {room_id}"

        logger.info(f"Successfully joined room {room_id}")
        return huddle_manager, True, "Room joined successfully"
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        return None, False, str(e)


def setup_room_manager_thread(room_id, project_id, api_key):
    """
    Sets up a thread to manage a Huddle01 room session with improved resource management.
    """
    result_container = {}

    def run_room_manager(room_id, result_dict):
        threading.current_thread().name = f"huddle-{room_id[:8]}"

        loop = asyncio.new_event_loop()

        def custom_exception_handler(loop, context):
            exception = context.get('exception')
            message = context.get('message')
            logger.error(f"Unhandled exception in event loop for room {room_id}: {message}")
            if exception:
                logger.exception("Exception details:", exc_info=exception)

        loop.set_exception_handler(custom_exception_handler)
        asyncio.set_event_loop(loop)

        huddle_manager = None
        join_result = None

        try:
            join_result = loop.run_until_complete(join_huddle_room(project_id, api_key, room_id, loop))
            huddle_manager, success, message = join_result

            if not success:
                result_dict['status_code'] = 500
                result_dict['message'] = message
                return
        except Exception as e:
            logger.error(f"Exception during room setup: {e}")
            result_dict['status_code'] = 500
            result_dict['message'] = f"Exception during setup: {str(e)}"
            loop.close()
            return

        logger.info("Room start successful")
        result_dict['status_code'] = 200
        result_dict['message'] = message
        result_dict['manager_thread'] = threading.current_thread()
        result_dict['loop'] = loop
        result_dict['manager'] = huddle_manager

        async def leave_room_async():
            try:
                if huddle_manager:
                    logger.info(f"Leaving room {room_id}...")
                    await huddle_manager.leave_room()
                    logger.info(f"Room {room_id} left successfully")
                    result_dict['leave_status'] = 200
                    result_dict['leave_message'] = "Room left successfully"
            except Exception as e:
                logger.error(f"Error leaving room: {e}")
                result_dict['leave_status'] = 500
                result_dict['leave_message'] = str(e)
            finally:
                gc.collect()
                loop.stop()

        def stop_callback():
            try:
                future = asyncio.run_coroutine_threadsafe(leave_room_async(), loop)
                # Add a timeout to avoid hanging
                future.result(timeout=10.0)
            except Exception as e:
                logger.error(f"Error in stop callback: {e}")
                # If the callback fails, try to forcibly close the loop
                try:
                    loop.stop()
                except:
                    pass

        if huddle_manager:
            huddle_manager.once("completed", leave_room_async)

        result_dict['stop_callback'] = stop_callback

        try:
            loop.run_forever()
        except Exception as e:
            logger.error(f"Error in event loop for room {room_id}: {e}")
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()

                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

                loop.close()
            except Exception as close_err:
                logger.error(f"Error closing event loop: {close_err}")
            finally:
                logger.info(f"Event loop for room {room_id} closed")
                gc.collect()

    thread = threading.Thread(target=run_room_manager, args=(room_id, result_container))
    thread.daemon = True
    thread.start()

    thread.join(timeout=5.0)

    return result_container
