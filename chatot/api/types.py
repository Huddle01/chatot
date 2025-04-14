from typing import TypedDict, Callable
from threading import Thread
import asyncio

from chatot.huddle.manager import Huddle01Manager

class SessionInfo(TypedDict):
    """
    Type definition for session information stored in the active_sessions dictionary.

    Attributes:
        thread: The thread managing the Huddle01 room session
        stop_callback: Function to call to stop the session
        manager: The Huddle01Manager instance
        loop: The asyncio event loop used by this session
        join_time: When the session was started (timestamp)
        last_activity: When the session last had activity (timestamp)
        metadata: Optional dictionary for additional session metadata
    """
    thread: Thread
    stop_callback: Callable[[], None]
    manager: Huddle01Manager
    loop: asyncio.AbstractEventLoop
