from huddle01 import HuddleClient, HuddleClientOptions
from huddle01.access_token import (
    Permissions,
    AccessToken,
    AccessTokenData,
    AccessTokenOptions,
    Role,
)
from huddle01.local_peer import LocalPeerEvents
from huddle01.room import RoomEvents, RoomEventsData, Room
from huddle01.handlers import ConsumeOptions

from pyee import AsyncIOEventEmitter
import json

from chatot.huddle.handlers import on_new_consumer
from chatot.log import base_logger

logger = base_logger.getChild(__name__)

class Huddle01Manager(AsyncIOEventEmitter):
    """
    Manager class for interacting with the Huddle01 API.

    This class provides methods for managing Huddle01 meetings, rooms,
    and other related functionalities.

    Attributes:
        project_id (str): The Huddle01 project ID.
        api_key (str): The API key for authentication with Huddle01 services.
    """

    def __init__(self, project_id: str, api_key: str, loop=None,):
        super(Huddle01Manager, self).__init__(loop=loop)
        self.project_id = project_id
        self.api_key = api_key
        options = HuddleClientOptions(autoConsume=False, volatileMessaging=False)
        self.client = HuddleClient(project_id=project_id, options=options)
        self.local_peer = None
        self.room = None
        self.peer_id = None

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
                role=Role.BOT,
                permissions=bot_permissions,
                options=access_token_options,
            )
            access_token = await AccessToken(access_token_data).to_jwt()

            room = await self.client.create(room_id=room_id, token=access_token)

            self.local_peer = room.local_peer
            self.peer_id = self.local_peer.peer_id

            @room.on(RoomEvents.RemoteProducerAdded)
            async def on_new_remote_producer(data: RoomEventsData.RemoteProducerAdded):
                if (data["label"] != "audio"):
                    logger.info(f"{data["label"]} found, ignoring..")
                else:
                    await room.local_peer.consume(options=ConsumeOptions(producer_id=data["producer_id"], producer_peer_id=data["remote_peer_id"]))

            @room.once(RoomEvents.RoomClosed)
            def on_room_close():
                logger.info("Room Closed, emitting completed")
                self.emit("completed")

            room.local_peer.on(LocalPeerEvents.NewConsumer, on_new_consumer)

            @room.on(RoomEvents.ConsumerClosed)
            async def on_consumer_closed(data: RoomEventsData.ConsumerClosed):
                logger.info(f"✅ Consumer Closed: {data['consumer_id']=}")

            await room.connect()
            return room
        except Exception as e:
            logger.error(e)
            raise

    async def leave_room(self):
        """
        Leave room by closing consumers and producer, close socket connection and reset state
        """
        if self.local_peer:
            await self.local_peer.close()
            self.room = None
            self.local_peer = None
            await self.client.close()

        logger.info("Room left successfully")
