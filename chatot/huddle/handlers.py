import pathlib
import asyncio

from huddle01.handlers.local_peer_handler import NewConsumerAdded
from chatot.recorder import WebRTCMediaRecorder
from chatot.uploader import upload_file
from chatot.utils.main import get_random_string
from chatot.utils.webhook_sender import WebhookSender

# Configure logging
from chatot.log import base_logger
logger = base_logger.getChild(__name__)

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
