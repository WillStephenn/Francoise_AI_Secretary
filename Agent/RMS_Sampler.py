import sys
import os
# Add the parent directory of 'Agent' to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import soundfile as sf
import numpy as np
import asyncio
import time
import pyaudio
from typing import AsyncGenerator
from Agent.config import RMS_SAMPLING_INTERVAL_MS, PROJECT_ROOT

def calculate_rms_from_bytes(audio_chunk_bytes: bytes) -> float:
    """
    Calculates the RMS value from a chunk of audio bytes.

    Args:
        audio_chunk_bytes: The chunk of audio data in bytes.
                           Expected to be in np.int16 format.

    Returns:
        float: The calculated RMS value. Returns 0.0 if the chunk is empty.
    """
    if not audio_chunk_bytes:
        return 0.0
    
    # Assuming audio_chunk_bytes are int16, as per AUDIO_FORMAT
    numpy_array = np.frombuffer(audio_chunk_bytes, dtype=np.int16)
    
    # Normalise to [-1.0, 1.0]
    float_array = numpy_array.astype(np.float32) / 32768.0
    
    # Calculate RMS
    rms = np.sqrt(np.mean(float_array**2))
    
    if np.isnan(rms): # Handle cases like all zeros after normalization if any issue
        return 0.0
    return rms
async def stream_audio_and_calculate_rms(audio_file_path: str, play_audio: bool = False) -> AsyncGenerator[float, None]:
    """
    Streams audio data from a file, calculates RMS values at specified intervals,
    yields them, optionally plays the audio, and optionally prints an RMS bar.

    Args:
        audio_file_path: The path to the audio file.
        play_audio: Whether to play the audio during processing.
    Yields:
        float: The calculated RMS value for each chunk.
    """
    p = None
    stream = None
    try:
        data, samplerate = sf.read(audio_file_path, dtype='float32') # Read as float32 for PyAudio
    except Exception as e:
        print(f"Error reading audio file: {e}")
        return

    if play_audio:
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, # Use paFloat32 for float32 data
                        channels=data.ndim, # Use number of channels from audio file
                        rate=samplerate,
                        output=True)

    samples_per_interval = int(samplerate * (RMS_SAMPLING_INTERVAL_MS / 1000.0))
    
    num_frames = len(data)
    current_pos = 0

    while current_pos < num_frames:
        start_time = time.monotonic()
        
        end_pos = min(current_pos + samples_per_interval, num_frames)
        chunk = data[current_pos:end_pos]
        
        if chunk.size == 0: # Skip empty chunks at the end
            break

        # Calculate RMS value for the current chunk
        rms_value = np.sqrt(np.mean(chunk**2))

        if play_audio and stream:
            # PyAudio expects bytes, so convert float32 numpy array to bytes
            # Ensure the audio data is in the correct format (float32)
            stream.write(chunk.tobytes())
        
        yield rms_value

        current_pos = end_pos

        processing_time = time.monotonic() - start_time
        await asyncio.sleep(max(0, (RMS_SAMPLING_INTERVAL_MS / 1000.0) - processing_time))

    if play_audio and stream:
        stream.stop_stream()
        stream.close()
    if play_audio and p:
        p.terminate()

async def main():
    """
    Main function to demonstrate audio streaming and RMS calculation.
    """
    audio_sample_path = os.path.join(PROJECT_ROOT, "Audio Samples", "How to make bread.wav")

    async for _rms_value in stream_audio_and_calculate_rms(audio_sample_path, play_audio=True):
        pass

if __name__ == "__main__":
    asyncio.run(main())
