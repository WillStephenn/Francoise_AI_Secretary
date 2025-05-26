import subprocess
import os
import sys
import asyncio
import socket
import time

# --- Configuration ---
# Set to "LIVE" to run Gemini Client, "FILE" to run with a sample audio file.
OPERATION_MODE = "FILE"  # Options: "LIVE" or "FILE"
# OPERATION_MODE = "LIVE" 

# Ensure Agent directory is in path for imports
# Correctly determine PROJECT_ROOT first to add to sys.path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Assuming run_visualiser_app.py is in the project root as per user request
_PROJECT_ROOT_FOR_SYS_PATH = _SCRIPT_DIR 
sys.path.insert(0, _PROJECT_ROOT_FOR_SYS_PATH)

from Agent.config import (
    RMS_SAMPLING_INTERVAL_MS,
    VISUALISER_EXE_PATH,
    GEMINI_CLIENT_SCRIPT_PATH,
    DEFAULT_SAMPLE_AUDIO_FILE,
    # PROJECT_ROOT is also available from config but not directly used here after imports
)
from Agent.RMS_Sampler import stream_audio_and_calculate_rms # For FILE mode

VISUALISER_UDP_HOST = "localhost"
VISUALISER_UDP_PORT = 12345  # Must match the port in visualiser.c

def start_c_visualiser():
    """Starts the C visualiser application."""
    if not os.path.exists(VISUALISER_EXE_PATH):
        print(f"Error: C Visualiser executable not found at {VISUALISER_EXE_PATH}")
        print("Please compile visualiser.c first (e.g., gcc Visualisation/visualiser.c -o Visualisation/visualiser -lm)")
        return None
    print(f"Starting C Visualiser: {VISUALISER_EXE_PATH}")
    try:
        visualiser_process = subprocess.Popen([VISUALISER_EXE_PATH])
        print(f"C Visualiser started with PID: {visualiser_process.pid}")
        time.sleep(1)  # Give it a moment to start up and bind the socket
        return visualiser_process
    except Exception as e:
        print(f"Failed to start C visualiser: {e}")
        return None

async def run_file_mode(visualiser_socket_sender):
    """Runs the visualiser with a sample audio file."""
    print(f"Running in FILE mode with: {DEFAULT_SAMPLE_AUDIO_FILE}")
    if not os.path.exists(DEFAULT_SAMPLE_AUDIO_FILE):
        print(f"Error: Sample audio file not found: {DEFAULT_SAMPLE_AUDIO_FILE}")
        return

    print(f"Streaming RMS from {DEFAULT_SAMPLE_AUDIO_FILE} to C visualiser at {VISUALISER_UDP_HOST}:{VISUALISER_UDP_PORT} and playing audio.")
    try:
        # stream_audio_and_calculate_rms already incorporates a delay based on RMS_SAMPLING_INTERVAL_MS
        async for rms_value in stream_audio_and_calculate_rms(DEFAULT_SAMPLE_AUDIO_FILE, play_audio=True):
            message = str(rms_value).encode('utf-8')
            visualiser_socket_sender.sendto(message, (VISUALISER_UDP_HOST, VISUALISER_UDP_PORT))
            # The C visualiser handles its own rendering rate.
            # The sleep is handled within stream_audio_and_calculate_rms.
    except Exception as e:
        print(f"Error during file mode: {e}")
    finally:
        print("File mode finished.")
        # Send a zero RMS to clear the bar
        try:
            visualiser_socket_sender.sendto("0.0".encode('utf-8'), (VISUALISER_UDP_HOST, VISUALISER_UDP_PORT))
        except Exception as e:
            print(f"Error sending final zero RMS: {e}")

def run_live_mode():
    """Runs the live conversation with Gemini Client."""
    print("Running in LIVE mode. Starting Gemini Client...")
    if not os.path.exists(GEMINI_CLIENT_SCRIPT_PATH):
        print(f"Error: Gemini Client script not found: {GEMINI_CLIENT_SCRIPT_PATH}")
        return None
    
    try:
        # Run Gemini Client. It should now be modified to send UDP packets.
        # Ensure the Python interpreter used here is the correct one for your environment.
        gemini_process = subprocess.Popen([sys.executable, GEMINI_CLIENT_SCRIPT_PATH])
        print(f"Gemini Client started with PID: {gemini_process.pid}")
        return gemini_process
    except Exception as e:
        print(f"Failed to start Gemini Client: {e}")
        return None

async def main_async_runner():
    visualiser_process = start_c_visualiser()
    if not visualiser_process:
        return

    # UDP Socket for sending RMS data (used by FILE mode directly, LIVE mode uses its own)
    udp_sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gemini_process_live = None

    try:
        if OPERATION_MODE == "FILE":
            await run_file_mode(udp_sender_socket)
        elif OPERATION_MODE == "LIVE":
            gemini_process_live = run_live_mode()
            if gemini_process_live:
                # Keep the main script alive while gemini_process_live (subprocess) is running
                while gemini_process_live.poll() is None:
                    await asyncio.sleep(0.5) # Check periodically
                print(f"Gemini Client process exited with code: {gemini_process_live.returncode}")
            else:
                print("Gemini client failed to start in LIVE mode.")
        else:
            print(f"Unknown OPERATION_MODE: {OPERATION_MODE}")

    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred in main_async_runner: {e}")
    finally:
        print("Shutting down...")
        if gemini_process_live and gemini_process_live.poll() is None:
            print("Terminating Gemini Client (if still running)...")
            gemini_process_live.terminate()
            try:
                gemini_process_live.wait(timeout=5) # Wait for graceful termination
            except subprocess.TimeoutExpired:
                print("Gemini Client did not terminate gracefully, killing.")
                gemini_process_live.kill()
            print("Gemini Client terminated.")
        
        if visualiser_process and visualiser_process.poll() is None:
            print("Terminating C Visualiser...")
            visualiser_process.terminate()
            try:
                visualiser_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("C Visualiser did not terminate gracefully, killing.")
                visualiser_process.kill()
            print("C Visualiser terminated.")
        
        udp_sender_socket.close()
        print("Cleanup complete. Exiting.")

if __name__ == "__main__":
    asyncio.run(main_async_runner())
