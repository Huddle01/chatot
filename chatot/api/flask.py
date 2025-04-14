import os

from flask import Flask, make_response, request, jsonify
from typing import Dict

from .huddle_service import setup_room_manager_thread
from .types import SessionInfo
from chatot.log import base_logger

logger = base_logger.getChild(__name__)

app = Flask(__name__)

# Store active room managers
active_sessions: Dict[str, SessionInfo] = {}

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
        logger.info(f"Room {room_id} already exists. Stopping it first.")
        session = active_sessions[room_id]
        try:
            session['stop_callback']()
            # Wait for the thread to complete
            session['thread'].join(timeout=5.0)
        except Exception as e:
            logger.error(f"Error cleaning up existing session: {e}")
        finally:
            del active_sessions[room_id]


    api_key = os.getenv("HUDDLE01_API_KEY")
    project_id = os.getenv("HUDDLE01_PROJECT_ID")

    if not api_key or not project_id:
        logger.error(
            "Missing required environment variables. Please set HUDDLE01_API_KEY, HUDDLE01_PROJECT_ID and ROOM_ID"
        )
        return jsonify({"error": "Invalid env setup"}), 500

    # Log current number of active sessions
    logger.info(f"Active sessions before adding new one: {len(active_sessions)}")

    # Setup room manager thread and get results
    result_container = setup_room_manager_thread(room_id, project_id, api_key)

    status_code = result_container.get('status_code', 500)
    message = result_container.get('message', "Unknown error or operation timed out")

    if status_code == 200:
        active_sessions[room_id] = {
            'thread': result_container['manager_thread'],
            'stop_callback': result_container['stop_callback'],
            'manager': result_container['manager'],
            'loop': result_container['loop']
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

    try:
        session['stop_callback']()
        # Wait for the thread to complete
        session['thread'].join(timeout=5.0)
    except Exception as e:
        logger.error(f"Error stopping room {room_id}: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error stopping room: {str(e)}"
        }), 500
    finally:
        # Always remove from active sessions, even if there was an error
        del active_sessions[room_id]
        logger.info(f"Room {room_id} removed from active sessions. Active count: {len(active_sessions)}")

    return jsonify({
        "status": "success",
        "message": f"Room {room_id} stopped successfully"
    }), 200
