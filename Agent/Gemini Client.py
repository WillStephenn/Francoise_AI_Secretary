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
    GEMINI_LIVE_CONNECT_CONFIG
)
# Import the RMS calculation function
from Agent.RMS_Sampler import calculate_rms_from_bytes

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

        # The LiveConnectConfig is now directly imported
        self.CONFIG = GEMINI_LIVE_CONNECT_CONFIG

        self._audio_input_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None
        self._audio_output_queue: Optional[asyncio.Queue[bytes]] = None

        self._session: Optional[Any] = None
        self._input_audio_stream: Optional[pyaudio.Stream] = None

    async def _listen_to_microphone(self) -> None:
        """
        Captures audio from the microphone and puts it into the input queue.
        
        Continuously reads audio data from the default microphone device and
        places it into the audio input queue for processing.
        """
        if self._audio_input_queue is None:
            print("Error: Audio input queue not initialised.")
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
        except asyncio.CancelledError:
            print("Microphone listening cancelled.")
        finally:
            if self._input_audio_stream:
                self._input_audio_stream.stop_stream()
                self._input_audio_stream.close()
            print("Microphone stream closed.")

    async def _send_audio_to_gemini(self) -> None:
        """
        Sends audio from the input queue to the Gemini API.
        
        Continuously takes audio chunks from the input queue and forwards
        them to the Gemini API session for processing.
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
        Receives audio from Gemini and puts it into the audio output queue.
        
        Listens for responses from the Gemini API and routes the audio
        data to the audio output queue.
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

                # Handle interruptions: clear audio queue
                while not self._audio_output_queue.empty():
                    self._audio_output_queue.get_nowait()
                    self._audio_output_queue.task_done()

        except asyncio.CancelledError:
            print("Receiving from Gemini cancelled.")
        except Exception as e:
            print(f"Error receiving from Gemini: {e}")
            traceback.print_exc()

    async def _play_received_audio(self) -> None:
        """
        Plays audio from the output queue using the speaker.
        
        Continuously retrieves audio chunks from the output queue and
        plays them through the default audio output device.
        Also calculates and prints RMS of the playing audio.
        """
        if self._audio_output_queue is None:
            print("Error: Audio output queue not initialised.")
            return

        output_audio_stream: Optional[pyaudio.Stream] = None
        try:
            output_audio_stream = await asyncio.to_thread(
                self._pya.open,
                format=AUDIO_FORMAT,
                channels=AUDIO_CHANNELS,
                rate=AUDIO_RECEIVE_SAMPLE_RATE,
                output=True,
            )
            print("Audio playback started.")
            while True:
                audio_chunk: bytes = await self._audio_output_queue.get()
                # Calculate and print RMS before writing to stream
                rms_value = calculate_rms_from_bytes(audio_chunk)
                print(f"Live RMS: {rms_value:.4f}") 
                await asyncio.to_thread(output_audio_stream.write, audio_chunk)
                self._audio_output_queue.task_done()
        except asyncio.CancelledError:
            print("Audio playback cancelled.")
        finally:
            if output_audio_stream:
                output_audio_stream.stop_stream()
                output_audio_stream.close()
            print("Audio playback stream closed.")

    async def run_conversation(self) -> None:
        """
        Runs the main conversation loop, managing all asynchronous tasks.
        
        Initialises the necessary queues, connects to the Gemini API, and
        coordinates the audio capture, sending, receiving, and playback tasks.
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
    
    Initialises and runs the GeminiClient, handling any interruptions
    or exceptions that may occur during execution.
    """
    client: GeminiClient = GeminiClient()
    try:
        await client.run_conversation()
    except KeyboardInterrupt:
        print("\nConversation interrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred in main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except Exception as e:
        print(f"Critical error in application startup: {e}")
        traceback.print_exc()
