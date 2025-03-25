from huddle01 import (
    AccessToken,
    AccessTokenData,
    AccessTokenOptions,
    HuddleClient,
    HuddleClientOptions,
    Role,
    Room,
)
import logging
import json

from huddle01.access_token import Permissions
from huddle01.local_peer import LocalPeerEvents
from huddle01.handlers.local_peer_handler import NewConsumerAdded
from huddle01.room import RoomEvents, RoomEventsData

from chatot.recorder import WebRTCMediaRecorder
import pathlib

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Huddle01Manager:
    """
    Manager class for interacting with the Huddle01 API.

    This class provides methods for managing Huddle01 meetings, rooms,
    and other related functionalities.

    Attributes:
        project_id (str): The Huddle01 project ID.
        api_key (str): The API key for authentication with Huddle01 services.
    """

    def __init__(self, project_id, api_key):
        self.project_id = project_id
        self.api_key = api_key
        options = HuddleClientOptions(autoConsume=True, volatileMessaging=False)
        self.client = HuddleClient(project_id=project_id, options=options)
        self.local_peer = None
        self.room = None

    async def join_room(self, room_id: str) -> Room:
        """
        Join a Huddle01 Room after creating a local peer
        """
        try:
            access_token_options: AccessTokenOptions = AccessTokenOptions(
                metadata=json.dumps({"displayName": "Chatot-Bot"})
            )
            bot_permissions = Permissions(admin=True)
            access_token_data: AccessTokenData = AccessTokenData(
                api_key=self.api_key,
                room_id=room_id,
                role=Role.HOST,
                permissions=bot_permissions,
                options=access_token_options,
            )
            access_token = await AccessToken(access_token_data).to_jwt()

            room = await self.client.create(room_id=room_id, token=access_token)

            await room.connect()
            self.local_peer = room.local_peer
            self.room = room

            @room.local_peer.on(LocalPeerEvents.NewConsumer)
            async def on_new_consumer(eventData: NewConsumerAdded):
                consumer = eventData["consumer"]
                remote_peer_id = eventData["remote_peer_id"]
                audioRecorder = None

                logger.info(f"✅ New consumer created: {consumer.id=}")

                if consumer.kind == "audio":
                    logger.info(
                        f"Audio consumer detected (ID: {consumer.id}), setting up recording"
                    )
                    track = consumer.track
                    format = "mp3"
                    if track:
                        audioRecorder = WebRTCMediaRecorder(
                            format=format,
                            output_path=f"{pathlib.Path().resolve()}/recordings/{remote_peer_id}.{format}",
                            track=track,
                        )
                        await audioRecorder.start()
                        logger.info("✅ Starting to record track")
                    else:
                        logger.warning("🔔 Track not found or not in ready state")

                    @consumer.observer.on("close")
                    async def on_close():
                        logger.info(
                            f"Consumer {consumer.id} closed, stopping recording"
                        )
                        if audioRecorder:
                            await audioRecorder.stop()
                        logger.info("✅ Recorder stopped")

            @room.on(RoomEvents.ConsumerClosed)
            async def on_consumer_closed(data: RoomEventsData.ConsumerClosed):
                logger.info(f"✅ Consumer Closed: {data['consumer_id']=}")

            return room
        except Exception as e:
            logger.error(f"Error creating room: {e}")
            raise

    async def leave_room(self):
        """
        Leave a Huddle01 room
        """
        if self.local_peer:
            await self.local_peer.close()

        logger.info("Room left successfully")
