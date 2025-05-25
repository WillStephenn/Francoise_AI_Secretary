import os
import pyaudio
from typing import List, Optional
from google.genai import types

# --- Path Configurations ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
ENV_FILE_PATH = os.path.join(SCRIPT_DIR, '.env')
SYSTEM_PROMPT_FILENAME = "System Prompt.md"

# --- Audio Configurations ---
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_SEND_SAMPLE_RATE = 16000
AUDIO_RECEIVE_SAMPLE_RATE = 24000
AUDIO_CHUNK_SIZE = 1024
# How often to sample audio RMS and send data to the ESP32 for display feedback
# during playback of Gemini's voice.
# Value is in milliseconds.
RMS_SAMPLING_INTERVAL_MS: int = 80

# --- Gemini Model & API Configurations ---
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-native-audio-dialog"
GEMINI_API_VERSION = "v1beta"

# --- LiveConnectConfig Parameters ---
GEMINI_RESPONSE_MODALITIES = ["AUDIO"]
GEMINI_MEDIA_RESOLUTION = "MEDIA_RESOLUTION_MEDIUM"
GEMINI_VOICE_NAME = "Gacrux"
GEMINI_CONTEXT_TRIGGER_TOKENS = 25600
GEMINI_CONTEXT_SLIDING_WINDOW_TARGET_TOKENS = 12800

def load_system_prompt(filename: str) -> str:
    """
    Loads the system prompt from the specified file.
    
    Args:
        filename: The name of the file containing the system prompt.
        
    Returns:
        str: The content of the system prompt file or a default prompt if file not found.
    """
    file_path = os.path.join(SCRIPT_DIR, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: System prompt file not found at {file_path}")
        return "You are a helpful assistant."  # Default fallback

SYSTEM_PROMPT = load_system_prompt(SYSTEM_PROMPT_FILENAME)

GEMINI_LIVE_CONNECT_CONFIG = types.LiveConnectConfig(
    response_modalities=GEMINI_RESPONSE_MODALITIES,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=GEMINI_VOICE_NAME)
        )
    ),
    system_instruction=types.Content(
        parts=[types.Part.from_text(text=SYSTEM_PROMPT)],
        role="user"
    ),
)
