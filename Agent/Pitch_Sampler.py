import sys
import os
# Add the parent directory of 'Agent' to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import soundfile as sf
import numpy as np
import asyncio
import time
import pyaudio
import librosa # For pitch detection
from typing import AsyncGenerator, Optional, Tuple

# Assuming config.py will have PITCH_SAMPLING_INTERVAL_MS
from Agent.config import (
    PITCH_SAMPLING_INTERVAL_MS,
    AUDIO_SEND_SAMPLE_RATE, # Example for live audio sample rate
    AUDIO_FORMAT as DEFAULT_AUDIO_FORMAT, # Example for live audio format
    PROJECT_ROOT
)

def calculate_pitch_from_float_array(audio_chunk_float: np.ndarray, sample_rate: int) -> int:
    """
    Calculates the fundamental frequency (pitch) from a chunk of audio data.

    Args:
        audio_chunk_float: The chunk of audio data as a numpy array of floats (mono).
        sample_rate: The sample rate of the audio chunk.

    Returns:
        int: The calculated pitch in Hz. Returns 0 if pitch cannot be detected or is NaN.
    """
    if audio_chunk_float.size == 0:
        return 0

    try:
        # Using librosa.pyin for pitch detection
        # fmin and fmax can be tuned based on expected pitch range (e.g., human voice)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio_chunk_float,
            fmin=librosa.note_to_hz('C2'), # Approx 65 Hz
            fmax=librosa.note_to_hz('C7'), # Approx 2093 Hz
            sr=sample_rate
        )

        pitch_hz = 0
        if f0 is not None and len(f0) > 0:
            valid_pitches = f0[~np.isnan(f0)]
            if len(valid_pitches) > 0:
                pitch_hz = int(np.mean(valid_pitches)) # Average valid pitches in the chunk
        return pitch_hz
    except Exception as e:
        # print(f"Error calculating pitch: {e}") # Optional: log error
        return 0

def calculate_pitch_from_bytes(audio_chunk_bytes: bytes, sample_rate: int, audio_format=DEFAULT_AUDIO_FORMAT) -> int:
    """
    Calculates the fundamental frequency (pitch) from a chunk of audio bytes.

    Args:
        audio_chunk_bytes: The chunk of audio data in bytes.
        sample_rate: The sample rate of the audio chunk.
        audio_format: The PyAudio format of the bytes (e.g., pyaudio.paInt16).

    Returns:
        int: The calculated pitch in Hz. Returns 0 if pitch cannot be detected.
    """
    if not audio_chunk_bytes:
        return 0

    if audio_format == pyaudio.paInt16:
        numpy_dtype = np.int16
        normalization_factor = 32768.0
    elif audio_format == pyaudio.paInt32:
        numpy_dtype = np.int32
        normalization_factor = 2147483648.0
    elif audio_format == pyaudio.paFloat32:
        numpy_dtype = np.float32
        normalization_factor = 1.0 # Already float
    else:
        print(f"Unsupported audio format for pitch calculation: {audio_format}")
        return 0

    numpy_array = np.frombuffer(audio_chunk_bytes, dtype=numpy_dtype)
    
    if numpy_dtype != np.float32:
        float_array = numpy_array.astype(np.float32) / normalization_factor
    else:
        float_array = numpy_array
    
    # If stereo, convert to mono by averaging channels. Librosa needs mono.
    if float_array.ndim > 1 and float_array.shape[1] > 1: # Check if it's multi-channel
         float_array = np.mean(float_array, axis=1)
    elif float_array.ndim > 1 and float_array.shape[1] == 1: # (N, 1) shape
         float_array = float_array.flatten()


    return calculate_pitch_from_float_array(float_array, sample_rate)

async def stream_audio_and_calculate_pitch(audio_file_path: str, play_audio: bool = False) -> AsyncGenerator[int, None]:
    """
    Streams audio data from a file, calculates pitch at specified intervals,
    yields them, and optionally plays the audio.

    Args:
        audio_file_path: The path to the audio file.
        play_audio: Whether to play the audio during processing.
    Yields:
        int: The calculated pitch value (frequency in Hz) for each chunk.
    """
    p = None
    player_stream = None
    try:
        data_for_playback, samplerate = sf.read(audio_file_path, dtype='float32', always_2d=False)
        
        if data_for_playback.ndim > 1: # If stereo or more channels
            # librosa.to_mono expects (channels, samples) if y.ndim > 1
            # soundfile reads (samples, channels)
            data_for_pitch = librosa.to_mono(data_for_playback.T)
        else:
            data_for_pitch = data_for_playback

    except Exception as e:
        print(f"Error reading audio file {audio_file_path}: {e}")
        return

    if play_audio:
        p = pyaudio.PyAudio()
        player_stream = p.open(format=pyaudio.paFloat32,
                               channels=data_for_playback.ndim if data_for_playback.ndim > 0 else 1,
                               rate=samplerate,
                               output=True)

    samples_per_interval = int(samplerate * (PITCH_SAMPLING_INTERVAL_MS / 1000.0))
    
    num_frames_pitch = len(data_for_pitch)
    # num_frames_playback = len(data_for_playback) # Not directly used in loop condition
    current_pos = 0

    while current_pos < num_frames_pitch:
        start_time = time.monotonic()
        
        end_pos = min(current_pos + samples_per_interval, num_frames_pitch)
        chunk_for_pitch_calc = data_for_pitch[current_pos:end_pos]
        
        if chunk_for_pitch_calc.size == 0:
            break

        pitch_value = calculate_pitch_from_float_array(chunk_for_pitch_calc, samplerate)
        
        if play_audio and player_stream:
            # For playback, use the corresponding chunk from original data
            # Ensure current_pos and end_pos are valid for data_for_playback if it had different length (e.g. stereo processing)
            # However, current_pos and end_pos are sample indices, so they should align.
            playback_chunk_end_pos = min(current_pos + samples_per_interval, len(data_for_playback))
            chunk_for_playback = data_for_playback[current_pos:playback_chunk_end_pos]
            if chunk_for_playback.size > 0:
                 player_stream.write(chunk_for_playback.tobytes())
        
        yield pitch_value

        current_pos = end_pos

        processing_time = time.monotonic() - start_time
        await asyncio.sleep(max(0, (PITCH_SAMPLING_INTERVAL_MS / 1000.0) - processing_time))

    if play_audio and player_stream:
        player_stream.stop_stream()
        player_stream.close()
    if play_audio and p:
        p.terminate()

async def main():
    """
    Main function to demonstrate audio streaming and pitch calculation.
    """
    audio_sample_filename = "Introduction.wav" # Or "How to make bread.wav"
    audio_sample_path = os.path.join(PROJECT_ROOT, "Audio Samples", audio_sample_filename)

    if not os.path.exists(audio_sample_path):
        print(f"Audio sample not found: {audio_sample_path}")
        # Try another common sample as a fallback for testing
        audio_sample_filename = "How to make bread.wav"
        audio_sample_path = os.path.join(PROJECT_ROOT, "Audio Samples", audio_sample_filename)
        if not os.path.exists(audio_sample_path):
            print(f"Fallback audio sample also not found: {audio_sample_path}")
            return
            
    print(f"Processing pitch for: {audio_sample_path}")
    
    async for pitch_hz in stream_audio_and_calculate_pitch(audio_sample_path, play_audio=False):
        if pitch_hz > 0:
            print(f"Detected Pitch: {pitch_hz} Hz")
    print(f"Finished pitch processing for {audio_sample_filename}.")

if __name__ == "__main__":
    asyncio.run(main())
