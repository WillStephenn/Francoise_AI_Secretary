# Françoise: AI Secretary

This project is a work-in-progress exploration into real-time, audio-to-audio conversational AI using Python and Google's Gemini API.

The primary focus is on the software agent and the technical challenges of creating a responsive, context-aware conversational experience. The project investigates two main areas: dynamic context management for live conversations and real-time audio stream processing.

---

## Core Features

* **Live Audio Conversation**: Utilises `asyncio` to handle bidirectional audio streaming with the Gemini API for a seamless conversational experience.
* **Dynamic Context Management**: The agent's system prompt is dynamically updated with the current UK date and time before each session, providing temporal awareness for more relevant responses.
* **Real-time Audio Analysis**: Includes experimental modules for processing audio chunks on-the-fly to calculate RMS volume and pitch frequency.

---

## Getting Started

### Prerequisites

* Python 3.11+
* A configured microphone and speakers
* A Google Gemini API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/WillStephenn/Francoise_AI_Secretary
    cd francoise_ai_secretary
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure your API key:**
    * Create a file named `.env` in the `Agent/` directory.
    * Add your Gemini API key to this file as follows:
        ```
        GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```

### Running the Agent

To start a conversation, execute the `Gemini Client.py` script from the project's root directory:

```bash
python Agent/Gemini\ Client.py
The application will connect to your default microphone. Start speaking to begin the interaction.

Future Work
The long-term vision is to embody this software agent in a physical, 3D-printed vintage telephone, using a Raspberry Pi to run the core logic and handle hardware interfacing.

The application will connect to your default microphone. Start speaking to begin the interaction.

Future Work
The long-term vision is to embody this software agent in a physical vintage telephone, using a Raspberry Pi to run the core logic and handle hardware interfacing.
