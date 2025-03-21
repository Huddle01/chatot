import wave
import logging
import os
from datetime import datetime
import numpy as np


logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SAMPLE_RATE = 48000 
CHANNELS = 1
SAMPLE_WIDTH = 2

class AudioRecorder:
    def __init__(self, directory="recordings"):
        self.directory = directory
        self.frames = []
        self.is_recording = False
        self.current_filename = None
        
        os.makedirs(directory, exist_ok=True)
        
    def generate_filename(self):
        """Generate a unique filename based on current timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        peer_id = "unknown" 
        return os.path.join(self.directory, f"audio_{timestamp}_{peer_id}.wav")
        
    def start_recording(self):
        self.frames = []
        self.is_recording = True
        self.current_filename = self.generate_filename()
        logger.info(f"Started recording to {self.current_filename}")
        
    def add_audio_data(self, audio_data):
        if self.is_recording:
            self.frames.append(audio_data)
            
    def stop_recording(self):
        if not self.is_recording or not self.current_filename:
            return

        self.is_recording = False
        
        with wave.open(self.current_filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            
            if self.frames:
                audio_data = np.concatenate(self.frames)
                wf.writeframes(audio_data.tobytes())
                
        logger.info(f"Recording saved to {self.current_filename}")
        return self.current_filename

