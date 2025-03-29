from typing import Callable, TypedDict
from threading import Thread

ThreadCallback = Callable[[], None]

class SessionInfo(TypedDict):
    thread: Thread
    stop_callback: ThreadCallback
