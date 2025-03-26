import logging
import asyncio
from aiortc.mediastreams import MediaStreamError
import av

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WebRTCMediaRecorder:
    """
    Records media from a RemoteStreamTrack to a file.
    """

    def __init__(self, track, output_path: str, format: str | None = None):
        """
        Initialize the recorder with a RemoteStreamTrack.

        Args:
            track: The RemoteStreamTrack object to record from.
            output_path: Path where the recorded file will be saved.
            format: Output format (determined from filename extension if None).
        """
        self.track = track
        self.output_path = output_path
        self.format = format
        self.recording = False
        self.task = None
        self.container = None
        self.stream = None

    async def start(self):
        """Start recording media."""
        if self.recording:
            return

        self.recording = True
        self.task = asyncio.create_task(self._record())

    async def stop(self):
        """Stop recording media."""
        if not self.recording:
            return

        self.recording = False
        if self.task:
            self.task.cancel()
            self.task = None

        if self.container:
            self.container.close()
            self.container = None
            self.stream = None

    async def _record(self):
        """Record media from the RemoteStreamTrack."""
        try:
            # Create output container
            self.container = av.open(self.output_path, mode="w", format=self.format)

            # Create appropriate stream
            if self.track.kind == "audio":
                self.stream = self.container.add_stream("mp3")
            else:
                logger.error("Cannot record video streams")
                return

            # Record frames
            while self.recording and self.track.readyState == "live":
                try:
                    frame = await self.track.recv()

                    # Encode and write the packet
                    for packet in self.stream.encode(frame):
                        self.container.mux(packet)
                except MediaStreamError:
                    logger.warn(
                        "No more frame available in track, exiting recording..."
                    )
                    break

        except asyncio.CancelledError:
            logger.info("Received Closing Signal")
        finally:
            # Flushing any remaining packets
            if self.container and self.stream:
                for packet in self.stream.encode(None):
                    self.container.mux(packet)

            if self.container:
                logger.info("Closing container")
                self.container.close()
                self.container = None
                self.stream = None
