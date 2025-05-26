import sys
import os
import platform
from typing import AsyncGenerator

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from Agent.RMS_Sampler import stream_audio_and_calculate_rms

# Constants for RMS bar visualisation
MAX_RMS_FOR_BAR = 0.4  # Estimated maximum RMS value for scaling the bar
BAR_WIDTH = 40  # Width of the RMS visualisation bar in characters
BAR_CHAR = '█' # Character to use for the bar

async def process_audio() -> None:
    """
    Processes audio from a specified file path and renders RMS visualisation.
    """
    audio_file_path = "/Users/will/Documents/Software Development/Françoise AI Secretary/Audio Samples/Introduction.wav"
    
    print(f"Starting audio processing for: {audio_file_path}")
    async for rms in stream_audio_and_calculate_rms(audio_file_path, play_audio=True):
        render_audio(rms_value=rms)
    print("Finished audio processing.")


def clear_terminal() -> None:
    """
    Clears the terminal screen based on the operating system.
    """
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def render_audio(rms_value: float) -> None:
    """
    Renders audio visualisation based on the RMS value.
    
    Args:
        rms_value: The RMS value to render as a visualisation bar.
    """
    clear_terminal() 
    print("---YOU ARE NOW CONNECTED TO FRANÇOISE---")
    scaled_rms = min(max(rms_value, 0), MAX_RMS_FOR_BAR) / MAX_RMS_FOR_BAR 
    bar_length = int(scaled_rms * BAR_WIDTH)
    rms_bar = BAR_CHAR * bar_length + ' ' * (BAR_WIDTH - bar_length)
    print(f"{rms_bar}")
    print("-"* BAR_WIDTH)
    
if __name__ == "__main__":
    asyncio.run(process_audio())