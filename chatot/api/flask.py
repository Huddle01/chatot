from flask import Flask, make_response, request, jsonify
import asyncio
from dotenv import load_dotenv
import os
from chatot.huddle import Huddle01Manager
import logging
import threading

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Store active room managers
active_sessions = {}

@app.route("/healthz", methods=['GET'])
async def hello_world():
    response = make_response('', 204)
    return response

@app.route("/start", methods=['GET'])
async def start_recording():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id parameter"}), 400

    if room_id in active_sessions:
        return jsonify({"status": "already_running", "message": f"Session for room {room_id} is already active"}), 409

    load_dotenv()

    api_key = os.getenv("HUDDLE01_API_KEY")
    project_id = os.getenv("HUDDLE01_PROJECT_ID")
    room_id = request.args.get('room_id')

    if not api_key or not project_id:
        logger.error(
            "Missing required environment variables. Please set HUDDLE01_API_KEY, HUDDLE01_PROJECT_ID and ROOM_ID"
        )
        return jsonify({"error": "Invalid env setup"}), 500

    result_container = {}

    # Function that will be executed in a separate thread
    def run_room_manager(room_id, result_dict):
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Function to join the room
        async def join_room():
            try:
                huddle_manager = Huddle01Manager(project_id=project_id, api_key=api_key)
                try:
                    result = await huddle_manager.join_room(room_id=room_id)
                except:
                    await huddle_manager.leave_room()
                    result = False

                if not result:
                    logger.error(f"Failed to join room {room_id}")
                    result_dict['status_code'] = 500
                    result_dict['message'] = f"Failed to join room {room_id}"
                    return None

                logger.info(f"Successfully joined room {room_id}")
                result_dict['status_code'] = 200
                result_dict['message'] = "Room joined successfully"
                return huddle_manager
            except Exception as e:
                logger.error(f"Error joining room: {e}")
                result_dict['status_code'] = 500
                result_dict['message'] = str(e)
                return None

        # Execute the join operation
        huddle_manager = loop.run_until_complete(join_room())

        # If join was successful, store the manager and loop in the thread
        if huddle_manager:
            # We need to keep the loop referenced for /stop to use later
            result_dict['manager_thread'] = threading.current_thread()
            result_dict['loop'] = loop
            result_dict['manager'] = huddle_manager

            # Create a stop event to signal when to terminate
            stop_event = threading.Event()
            result_dict['stop_event'] = stop_event

            async def keep_alive():
                while not stop_event.is_set():
                    # This allows the websocket to receive and process messages
                    await asyncio.sleep(0.1)  # Short sleep to avoid CPU hogging

                try:
                    await huddle_manager.leave_room()
                    logger.info(f"Room {room_id} left successfully")
                    result_dict['leave_status'] = 200
                    result_dict['leave_message'] = "Room left successfully"
                except Exception as e:
                    logger.error(f"Error leaving room: {e}")
                    result_dict['leave_status'] = 500
                    result_dict['leave_message'] = str(e)

            try:
                # Run the keep_alive coroutine until it completes
                loop.run_until_complete(keep_alive())
            finally:
                loop.close()
        else:
            loop.close()

    thread = threading.Thread(target=run_room_manager, args=(room_id, result_container))

    # Make it a daemon thread so it exits when main program exits
    thread.daemon = True
    thread.start()

    # Wait a short time for the join operation to complete
    thread.join(timeout=5.0)

    status_code = result_container.get('status_code', 500)
    message = result_container.get('message', "Unknown error or operation timed out")

    if status_code == 200:
        active_sessions[room_id] = {
            'thread': result_container['manager_thread'],
            'stop_event': result_container['stop_event']
        }

        return jsonify({
            "status": "success",
            "message": message
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": message
        }), status_code

@app.route("/stop", methods=['GET'])
async def stop_room():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({"error": "Missing room_id parameter"}), 400

    if room_id not in active_sessions:
        return jsonify({"status": "not_found", "message": f"No active session for room {room_id}"}), 404

    session = active_sessions[room_id]

    session['stop_event'].set()

    # Wait for the thread to complete
    session['thread'].join(timeout=2.0)

    del active_sessions[room_id]

    return jsonify({
        "status": "success",
        "message": f"Room {room_id} stopped successfully"
    }), 200
