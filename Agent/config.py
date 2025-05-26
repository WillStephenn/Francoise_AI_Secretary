import os
import pyaudio
from typing import List, Optional
from google.genai import types

# Import the new context builder
from Agent.context_builder import get_contextual_system_prompt

# --- Path Configurations ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
ENV_FILE_PATH = os.path.join(SCRIPT_DIR, '.env')
SYSTEM_PROMPT_FILENAME = "System Prompt.md" # Relative to SCRIPT_DIR (Agent folder)
SYSTEM_PROMPT_PATH = os.path.join(SCRIPT_DIR, SYSTEM_PROMPT_FILENAME)

# --- Application Structure Paths (relative to PROJECT_ROOT) ---
VISUALISER_DIR_NAME = "Visualisation"
VISUALISER_EXE_NAME = "Visualiser.out" # Changed from "visualiser"
AGENT_DIR_NAME = "Agent" # For consistency, though SCRIPT_DIR is often used for this
GEMINI_CLIENT_SCRIPT_NAME = "Gemini Client.py"
AUDIO_SAMPLES_DIR_NAME = "Audio Samples"
DEFAULT_SAMPLE_AUDIO_FILENAME = "How to make bread.wav"

# --- Full Paths derived from PROJECT_ROOT ---
VISUALISER_DIR = os.path.join(PROJECT_ROOT, VISUALISER_DIR_NAME)
VISUALISER_EXE_PATH = os.path.join(VISUALISER_DIR, VISUALISER_EXE_NAME)
AGENT_DIR = os.path.join(PROJECT_ROOT, AGENT_DIR_NAME)
GEMINI_CLIENT_SCRIPT_PATH = os.path.join(AGENT_DIR, GEMINI_CLIENT_SCRIPT_NAME)
AUDIO_SAMPLES_DIR = os.path.join(PROJECT_ROOT, AUDIO_SAMPLES_DIR_NAME)
DEFAULT_SAMPLE_AUDIO_FILE = os.path.join(AUDIO_SAMPLES_DIR, DEFAULT_SAMPLE_AUDIO_FILENAME)

# --- Visualiser Network Configurations ---
VISUALISER_UDP_HOST = "localhost"
VISUALISER_UDP_PORT = 12345

# --- Audio Configurations ---
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_SEND_SAMPLE_RATE = 16000
AUDIO_RECEIVE_SAMPLE_RATE = 24000
AUDIO_CHUNK_SIZE = 1024
# How often to sample audio RMS and send data to the ESP32 for display feedback
# during playback of Gemini's voice.
# Value is in milliseconds.
RMS_SAMPLING_INTERVAL_MS: int = 100
PITCH_SAMPLING_INTERVAL_MS: int = 100

# --- Feature Toggles ---
ENABLE_RMS_PROCESSING: bool = True
ENABLE_PITCH_PROCESSING: bool = False

# --- Gemini Model & API Configurations ---
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-native-audio-dialog"
GEMINI_API_VERSION = "v1beta"

# --- LiveConnectConfig Parameters ---
GEMINI_RESPONSE_MODALITIES = ["AUDIO"]
GEMINI_MEDIA_RESOLUTION = "MEDIA_RESOLUTION_MEDIUM"
GEMINI_VOICE_NAME = "Gacrux"
GEMINI_CONTEXT_TRIGGER_TOKENS = 25600
GEMINI_CONTEXT_SLIDING_WINDOW_TARGET_TOKENS = 12800
GEMINI_TOOLS = [
    types.Tool(google_search=types.GoogleSearch()),
]

SYSTEM_PROMPT = get_contextual_system_prompt() # Use the new function


GEMINI_LIVE_CONNECT_CONFIG = types.LiveConnectConfig(
    response_modalities=GEMINI_RESPONSE_MODALITIES,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=GEMINI_VOICE_NAME)
        )
    ),
    tools=GEMINI_TOOLS,
    media_resolution=GEMINI_MEDIA_RESOLUTION,
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=GEMINI_CONTEXT_TRIGGER_TOKENS,
        sliding_window=types.SlidingWindow(target_tokens=GEMINI_CONTEXT_SLIDING_WINDOW_TARGET_TOKENS),
    ),
    system_instruction=types.Content(
        parts=[types.Part.from_text(text=SYSTEM_PROMPT)],
        role="user"
    ),
)
