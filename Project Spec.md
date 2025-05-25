# Project Spec: Françoise, AI Secretary Phone

## 1. Project Vision & Goal

* **Vision:** To create an affordable, highly expressive, and voice-interactive 3D-printed vintage telephone AI assistant.
* **Goal:** The device will engage in spoken conversations using Google's Gemini native audio models. Its primary mode of emotional expression will be through an information display on an integrated screen, showing emotions derived from Gemini's responses. It will be housed within a modified vintage telephone enclosure.

## 2. Core Features

* Conversational sessions initiated by lifting the handset or pressing a designated button on the telephone.
* Live audio input to Gemini via the telephone's original handset microphone (interfaced with an ADC).
* Native audio speech output from Gemini via the telephone's original handset speaker (driven by an amplifier).
* **Primary Emotional Expression:** Information display on an ESP32-driven screen, showing emotion indicators derived from Gemini's responses.
* Custom-trained audio sentence-to-emotion classifier running on the Raspberry Pi.
* Tightly integrated hardware design within a modified vintage telephone enclosure, potentially using 3D printed internal mounts.

## 3. Technology Stack

* **Cloud AI Service:** Google Gemini API (e.g., `gemini-2.5-flash-preview-native-audio-dialog`).
* **Primary Application Logic (Raspberry Pi):** Python 3.
* **Display & Low-Level Control (ESP32):** C/C++ (Arduino IDE or ESP-IDF).
* **Emotion Classification Model:** Custom-trained text classifier (e.g., Scikit-learn, TensorFlow Lite) deployed on Raspberry Pi.
* **Key Python Libraries (Raspberry Pi):**
    * `google-generativeai`
    * `pyserial` or RPi.GPIO for UART communication
    * ALSA utilities / `sounddevice` / `PyAudio` (for ADC/DAC interfacing or I2S if chosen over original components)
    * Machine learning libraries for emotion model inference (e.g., `scikit-learn`, `tensorflow-lite-runtime`)
    * GPIO library (e.g., `RPi.GPIO` or `gpiozero`) for button/hook switch input
* **Key ESP32 Libraries:** Display driver (e.g., `TFT_eSPI`, `LovyanGFX`), graphics rendering, serial communication.

## 4. Key Hardware Components & Roles

### A. Raspberry Pi (The Brain & Sensory Hub)

* **Model:** Raspberry Pi 4 Model B / Raspberry Pi 5 (or Pi 3B+).
* **Responsibilities:**
    * Internet connectivity (Wi-Fi/Ethernet).
    * Running main Python application.
    * Full Gemini API interaction (audio streaming, response handling).
    * Receiving and processing text from Gemini for emotion analysis.
    * Running the sentence-to-emotion classifier.
    * Analysing its own audio output (Gemini's voice) for dB levels (potentially for subtle visual feedback on the display, if desired, but not full mouth sync).
    * Sending high-level display commands (emotion, status information) to the ESP32.
    * Handling input from the telephone's hook switch and/or buttons via GPIO or through the ESP32.
* **Integrated Peripherals:**
    * **Microphone Input:** Original telephone handset microphone, connected to an ADC (Analog-to-Digital Converter) interfaced with the Raspberry Pi (e.g., via I2C or SPI), or an I2S microphone if the original proves too difficult to interface well.
    * **Speaker Output:** Original telephone handset speaker, driven by an amplifier connected to a DAC (Digital-to-Analog Converter) interfaced with the Raspberry Pi (e.g., via I2C, SPI, or a dedicated audio DAC HAT), or an I2S DAC/Amp module if preferred.
    * Removed: Camera

### B. ESP32 with Integrated Display (The Display & Input Handler)

* **Model:** ESP32 module with a built-in colour TFT/OLED display.
* **Responsibilities:**
    * Receiving display commands from the Raspberry Pi.
    * Rendering information and emotion indicators on its display.
    * Reading the telephone's hook switch and/or buttons and sending state changes to the Raspberry Pi (if not directly connected to Pi GPIO).
* **Connected Peripherals:**
    * The integrated display itself.
    * Connection to the telephone's hook switch and any designated buttons.

### C. Supporting Components

* **Speaker:** Original telephone handset speaker.
* **Microphone:** Original telephone handset microphone.
* **ADC/DAC & Amplifier:** Suitable ADC for the microphone and DAC/Amplifier for the speaker to interface with the Raspberry Pi.
* **Chassis:** Modified vintage telephone enclosure, potentially with 3D printed internal mounts.
* **Power Supply:** Stable 5V, 3A+ power source for the Raspberry Pi, with power distributed to the ESP32 module and other components.

## 5. Integration Points & Communication Protocols

* **Raspberry Pi <-> Google Gemini API:** Secure HTTPS.
* **Raspberry Pi (Audio Input):** Original Handset Mic -> ADC -> Pi (e.g., I2C/SPI/GPIO).
* **Raspberry Pi (Audio Output for Playback & Analysis):** Pi (e.g., I2C/SPI/GPIO) -> DAC -> Amplifier -> Original Handset Speaker. (Python script analyses this stream before/during playback).
* **Raspberry Pi <-> ESP32:**
    * **Physical Link:** Serial (UART) connection (Pi GPIO TX/RX <-> ESP32 RX/TX). Logic level shifting if voltages differ.
    * **Protocol:** Custom serial messages (e.g., JSON strings or simple delimited commands like `"DISPLAY:HAPPY"`, `"EVENT:HOOK_OFF"`, `"EVENT:BUTTON_1_PRESS"`).

## 6. Development Strategy & Phased Rollout

* **Phase 1: Core Software (Laptop Development):**
    * **Gemini Interaction Module (Python):** Develop and test Gemini communication, audio I/O (using laptop mic/speakers), and text response capture.
    * **Sentence-to-Emotion Classifier (Python):**
        * Generate sentence-emotion dataset using an LLM.
        * Train, evaluate, and save the classification model.
        * Create an inference function.
    * **Audio Analysis (Python):** Develop logic to derive dB levels from audio being played (for potential subtle visual feedback).
    * **Simulated ESP32 Information Display (Python GUI or C/C++ Window on Laptop):** Create a window to visualise information and emotion indicators based on commands.
    * **Button/Hook Switch Input Simulation (Python):** Simulate inputs for starting/ending sessions.
    * **Main Orchestration Script (Python):** Integrate all above modules on the laptop.

* **Phase 2: Raspberry Pi Integration:**
    * Port Python application to Raspberry Pi.
    * Integrate ADC for microphone input from telephone handset.
    * Integrate DAC/Amplifier for speaker output to telephone handset.
    * Integrate hook switch and button inputs via GPIO or ESP32.
    * Test the emotion classifier and mouth sync logic on the Pi.

* **Phase 3: ESP32 Display Firmware & Communication:**
    * Develop ESP32 firmware to:
        * Initialise and control its display.
        * Render different emotion indicators and status information.
        * Handle hook switch/button input and relay to Pi (if ESP32 is managing these inputs).
    * Establish and test robust serial communication between Pi and ESP32.

* **Phase 4: Full System Assembly & Testing:**
    * Assemble all components into the modified telephone enclosure.
    * End-to-end testing: Handset lifted/button press -> Pi & Gemini interaction -> Emotion classification -> Information display on ESP32.
    * Refine timings, animations, and overall responsiveness.

## 7. Success Criteria / Desired Outcomes

* Device initiates conversation and responds coherently via Gemini when the handset is lifted or a designated button is pressed.
* ESP32 display clearly shows distinct emotion indicators and relevant status information corresponding to the classified emotion of Gemini's responses.
* Interaction latency is acceptable for a conversational experience.
* Hardware is neatly integrated into the vintage telephone enclosure.
* The custom emotion classifier performs with satisfactory accuracy.

## 8. Potential Challenges & Risks

* **Gemini API Free Tier Limits:** Especially RPD for relevant models.
* **Emotion Classifier Accuracy & Nuance:** Achieving good performance that feels natural.
* **Audio Interfacing:** Successfully interfacing the original telephone microphone and speaker with the Raspberry Pi (ADC/DAC quality, noise levels).
* **I2S Configuration on Pi:** Can be complex for both input and output (if I2S components are chosen over ADC/DAC for original phone parts).
* **Real-time Performance on Pi:** Balancing AI processing, audio analysis, and communication.
* **Pi-ESP32 Serial Communication:** Ensuring robustness and speed.
* **Power Management:** Stable power for all components.
* **Latency:** Cumulative latency from all processing steps.

## Instructions for Co-Pilot:

Always include docstrings for functions and methods.
Docstrings should contain:
- A brief, one-line description of what the function does.
- A section detailing each argument (`Args:`), its name, and description. Only include Args if they are not None.
- A section detailing the return value (`Returns:`), its type, and description. Only include Returns if they are not None.
Follow the standard docstring format for the language being used (e.g., Python's reST or Google style, JSDoc for JavaScript).

Always include type hints for function and method parameters when writing in Python.
Always include type hints for function and method return values when writing in Python.
Never include redundant comments denoting edits made such as "changed this" or "import x".

Always use UK english, not USA english.

Build code in a modular way from the start, with smaller already refactored files rather than monolithic files.

You have all the google documentation for the Gemini API in ./Google Documentation. It is up to date, so always refer to it.