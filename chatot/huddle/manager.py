import asyncio
from huddle01 import HuddleClient, HuddleClientOptions
from huddle01.access_token import (
    Permissions,
    AccessToken,
    AccessTokenData,
    AccessTokenOptions,
    Role,
)
from huddle01.local_peer import LocalPeerEvents
from huddle01.handlers.local_peer_handler import NewConsumerAdded
from huddle01.room import RoomEvents, RoomEventsData, Room
from huddle01.handlers import ConsumeOptions

from chatot.recorder import WebRTCMediaRecorder
from chatot.uploader import upload_file
from chatot.utils.main import get_random_string
from chatot.utils.webhook_sender import WebhookSender

from pyee import AsyncIOEventEmitter

import logging
import json
import pathlib

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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

            await room.connect()
            self.local_peer = room.local_peer
            self.peer_id = self.local_peer.peer_id
            self.room = room

            remote_peers = self.local_peer.remote_peers

            for _, peer in remote_peers.items():
                audio_producer = peer.label_to_producers["audio"]
                if audio_producer:
                    await self.local_peer.consume(options=ConsumeOptions(producer_id=audio_producer.producer_id, producer_peer_id=audio_producer.peer_id))

            @room.on(RoomEvents.RemoteProducerAdded)
            async def on_new_remote_producer(data: RoomEventsData.RemoteProducerAdded):
                if (data["label"] != "audio"):
                    logger.info(f"{data["label"]} found, ignoring..")
                    return

                if self.local_peer:
                    await self.local_peer.consume(options=ConsumeOptions(producer_id=data["producer_id"], producer_peer_id=data["remote_peer_id"]))

            @room.once(RoomEvents.RoomClosed)
            def on_room_close():
                logger.info("Room Closed, emitting completed")
                self.emit("completed")

            @room.local_peer.on(LocalPeerEvents.NewConsumer)
            async def on_new_consumer(eventData: NewConsumerAdded):
                consumer = eventData["consumer"]
                remote_peer_id = eventData["remote_peer_id"]
                audioRecorder = None

                logger.info(f"✅ New consumer created: {consumer.id=}")

                if consumer.kind and consumer.kind.value == "audio":
                    logger.info(
                        f"Audio consumer detected (ID: {consumer.id}), setting up recording"
                    )
                    track = consumer.track
                    format = "mp3"
                    audio_file_name = f"{remote_peer_id}-{get_random_string(4)}.{format}"
                    audio_file_path = f"{pathlib.Path().resolve()}/recordings/{audio_file_name}"

                    if track:
                        logger.info(f"✅ Starting to record track: {audio_file_name}")

                        audioRecorder = WebRTCMediaRecorder(
                            format=format,
                            output_path=audio_file_path,
                            track=track,
                            loop=asyncio.get_event_loop()
                        )
                        await audioRecorder.start()

                        def on_recording_complete():
                            logger.info("⬆️ Uploading file to bucket")

                            try:
                                uploaded_file_url = upload_file(
                                    file_name=audio_file_path,
                                    object_name=f"recordings/{audio_file_name}"
                                )
                                logger.info(f"Uploaded file url: {uploaded_file_url}")
                                webhook_sender = WebhookSender(endpoint_url=None)
                                webhook_sender.send_webhook(peer_id=remote_peer_id, audio_file_url=uploaded_file_url)
                            except Exception as e:
                                logger.error(f"Error uploading file: {e}")

                        audioRecorder.once("completed", on_recording_complete)
                    else:
                        logger.warning("🔔 Track not found or not in ready state")

                    @consumer._observer.on("close")
                    async def on_close():
                        logger.info(
                            f"Consumer {consumer.id} closed, stopping recording"
                        )
                        if audioRecorder:
                            await audioRecorder.stop()

            @room.on(RoomEvents.ConsumerClosed)
            async def on_consumer_closed(data: RoomEventsData.ConsumerClosed):
                logger.info(f"✅ Consumer Closed: {data['consumer_id']=}")

            return room
        except Exception as e:
            logger.error(f"Error creating room: {e}")
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
