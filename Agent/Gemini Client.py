"""
Handles all interactions with the Google Gemini API for audio and text.
"""

import sys
import os
# Add the parent directory of 'Agent' (which is the project root) to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import traceback
from typing import Dict, Any, Optional

import pyaudio
from dotenv import load_dotenv
from google import genai

# Import configurations from config.py
from Agent.config import (
    ENV_FILE_PATH,
    AUDIO_FORMAT,
    AUDIO_CHANNELS,
    AUDIO_SEND_SAMPLE_RATE,
    AUDIO_RECEIVE_SAMPLE_RATE,
    AUDIO_CHUNK_SIZE,
    GEMINI_MODEL_NAME,
    GEMINI_API_VERSION,
    GEMINI_LIVE_CONNECT_CONFIG,
    VISUALISER_UDP_HOST,
    VISUALISER_UDP_PORT,
    ENABLE_RMS_PROCESSING,    # Added
    ENABLE_PITCH_PROCESSING # Added
)
from Agent.RMS_Sampler import calculate_rms_from_bytes
from Agent.Pitch_Sampler import calculate_pitch_from_bytes # Added
import socket

load_dotenv(ENV_FILE_PATH)

if sys.version_info < (3, 11, 0):
    import taskgroup
    import exceptiongroup

    asyncio.TaskGroup = taskgroup.TaskGroup # type: ignore
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup # type: ignore


class GeminiClient:
    """
    Manages audio input/output and communication with the Gemini API.
    """

    def __init__(self) -> None:
        """
        Initialises the GeminiClient with necessary audio interfaces and API configuration.
        
        Raises:
            ValueError: If the GEMINI_API_KEY environment variable is not set.
        """
        self._pya: pyaudio.PyAudio = pyaudio.PyAudio()
        api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Make sure it's set in your .env file.")
        self._client: genai.Client = genai.Client(
            http_options={"api_version": GEMINI_API_VERSION},
            api_key=api_key,
        )

        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._visualiser_address = (VISUALISER_UDP_HOST, VISUALISER_UDP_PORT)

        self.CONFIG = GEMINI_LIVE_CONNECT_CONFIG

        self._audio_input_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None
        self._audio_output_queue: Optional[asyncio.Queue[bytes]] = None

        self._session: Optional[Any] = None
        self._input_audio_stream: Optional[pyaudio.Stream] = None

    async def _listen_to_microphone(self) -> None:
        """
        Captures audio from the microphone and puts it into the input queue.
        """
        if self._audio_input_queue is None:
            print("Error: Audio input queue is not initialised.")
            return

        mic_info: Dict[str, Any] = self._pya.get_default_input_device_info()
        self._input_audio_stream = await asyncio.to_thread(
            self._pya.open,
            format=AUDIO_FORMAT,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=AUDIO_CHUNK_SIZE,
        )
        if __debug__:
            kwargs: Dict[str, bool] = {"exception_on_overflow": False}
        else:
            kwargs = {}

        print("Listening...")
        try:
            while True:
                data: bytes = await asyncio.to_thread(
                    self._input_audio_stream.read, AUDIO_CHUNK_SIZE, **kwargs
                )
                await self._audio_input_queue.put({"data": data, "mime_type": "audio/pcm"})

                rms_value: float = 0.0
                pitch_value: int = 0

                if ENABLE_RMS_PROCESSING: # Added
                    rms_value = calculate_rms_from_bytes(data)
                if ENABLE_PITCH_PROCESSING: # Added
                    try:
                        pitch_value = calculate_pitch_from_bytes(data, sample_rate=AUDIO_SEND_SAMPLE_RATE, audio_format=AUDIO_FORMAT)
                    except Exception as e:
                        print(f"Error calculating pitch in _listen_to_microphone: {e}")
                        pitch_value = 0 # Default to 0 if calculation fails
                
                message: bytes = f"{rms_value},{pitch_value}".encode('utf-8')
                self._udp_socket.sendto(message, self._visualiser_address)

        except asyncio.CancelledError:
            print("Microphone listening task cancelled.")
        finally:
            if self._input_audio_stream:
                self._input_audio_stream.stop_stream()
                self._input_audio_stream.close()
            print("Microphone stream closed.")

    async def _send_audio_to_gemini(self) -> None:
        """
        Sends audio from the input queue to the Gemini API.
        """
        if self._audio_input_queue is None or self._session is None:
            print("Error: Audio input queue or session not initialised for sending.")
            return

        try:
            while True:
                audio_chunk: Dict[str, Any] = await self._audio_input_queue.get()
                await self._session.send_realtime_input(audio=audio_chunk)
                self._audio_input_queue.task_done()
        except asyncio.CancelledError:
            print("Audio sending to Gemini cancelled.")
        except Exception as e:
            print(f"Error sending audio to Gemini: {e}")
            traceback.print_exc()

    async def _receive_from_gemini(self) -> None:
        """
        Receives audio and text from Gemini, puts audio into the output queue, and prints text.
        """
        if self._audio_output_queue is None or self._session is None:
            print("Error: Audio output queue or session not initialised for receiving.")
            return

        print("Receiving from Gemini...")
        try:
            while True:
                turn: Any = self._session.receive()
                async for response in turn:
                    if audio_data := response.data:
                        self._audio_output_queue.put_nowait(audio_data)
                    if text_data := response.text:
                        print(text_data, end="")  # Print received text

                # If you interrupt the model, it sends a turn_complete.
                # For interruptions to work, we need to stop playback.
                # So empty out the audio queue because it may have loaded
                # much more audio than has played yet.
                while not self._audio_output_queue.empty():
                    self._audio_output_queue.get_nowait()
                    self._audio_output_queue.task_done() # Ensure task_done is called for each get

        except asyncio.CancelledError:
            print("Receiving from Gemini cancelled.")
        except Exception as e:
            print(f"Error receiving from Gemini: {e}")
            traceback.print_exc()

    async def _play_received_audio(self) -> None:
        """
        Plays audio from the output queue using the speaker.
        """
        if self._audio_output_queue is None:
            print("Error: Audio output queue is not initialised.")
            return

        output_audio_stream: Optional[pyaudio.Stream] = await asyncio.to_thread(
            self._pya.open,
            format=AUDIO_FORMAT,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            print("Audio playback started.")
            while True:
                audio_chunk_bytes: bytes = await self._audio_output_queue.get()
                await asyncio.to_thread(output_audio_stream.write, audio_chunk_bytes)
                self._audio_output_queue.task_done()

                rms_value: float = 0.0
                pitch_value: int = 0

                if ENABLE_RMS_PROCESSING: # Added
                    rms_value = calculate_rms_from_bytes(audio_chunk_bytes)
                if ENABLE_PITCH_PROCESSING: # Added to correctly calculate pitch for visualiser
                    try:
                        pitch_value = calculate_pitch_from_bytes(audio_chunk_bytes, sample_rate=AUDIO_RECEIVE_SAMPLE_RATE, audio_format=AUDIO_FORMAT)
                    except Exception as e:
                        print(f"Error calculating pitch in _play_received_audio: {e}")
                        pitch_value = 0 # Default to 0 if calculation fails
                
                message: bytes = f"{rms_value},{pitch_value}".encode('utf-8')
                self._udp_socket.sendto(message, self._visualiser_address)

        except asyncio.CancelledError:
            print("Audio playback task cancelled.")
        finally:
            if output_audio_stream:
                output_audio_stream.stop_stream()
                output_audio_stream.close()
            print("Audio playback stream closed.")

    async def run_conversation(self) -> None:
        """
        Runs the main conversation loop, managing all asynchronous tasks.
        """
        self._audio_input_queue = asyncio.Queue(maxsize=10)
        self._audio_output_queue = asyncio.Queue()

        try:
            async with (
                self._client.aio.live.connect(model=GEMINI_MODEL_NAME, config=self.CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self._session = session
                print("Gemini session started.")

                mic_task: asyncio.Task[None] = tg.create_task(self._listen_to_microphone())
                send_task: asyncio.Task[None] = tg.create_task(self._send_audio_to_gemini())
                receive_task: asyncio.Task[None] = tg.create_task(self._receive_from_gemini())
                play_task: asyncio.Task[None] = tg.create_task(self._play_received_audio())

                await asyncio.gather(mic_task, send_task, receive_task, play_task, return_exceptions=True)

        except asyncio.CancelledError:
            print("Conversation run cancelled.")
        except asyncio.ExceptionGroup as eg: # type: ignore
            print("Exception group caught in run_conversation:")
            traceback.print_exception(eg)
        except Exception as e:
            print(f"An unexpected error occurred in run_conversation: {e}")
            traceback.print_exc()
        finally:
            print("Cleaning up PyAudio...")
            self._pya.terminate()
            print("PyAudio terminated. Exiting.")


async def main() -> None:
    """
    Main function to run the Gemini client.
    """
    client: GeminiClient = GeminiClient()
    try:
        await client.run_conversation()
    except KeyboardInterrupt:
        print("\nShutting down Gemini Client...")
    except Exception as e:
        print(f"An error occurred in main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print("\nExiting main program...")
    except Exception as e:
        print(f"Critical error in application startup: {e}")
        traceback.print_exc()
