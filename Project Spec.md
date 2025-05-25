# Project Spec: Jean-Pierre, AI Desktop Companion

## 1. Project Vision & Goal

* **Vision:** To create an affordable, highly expressive, and voice-interactive 3D-printed desktop robot companion.
* **Goal:** The robot will engage in spoken conversations using Google's Gemini native audio models. Its primary mode of emotional expression will be through an animated face on an integrated display, driven by a custom-trained emotion classifier. It will also feature synchronised mouth movements on the display based on audio output.

## 2. Core Features

* Button-initiated conversational sessions with Gemini.
* Live audio and video input to Gemini.
* Native audio speech output from Gemini.
* **Primary Emotional Expression:** Animated face on an ESP32-driven display, showing emotions derived from Gemini's responses.
* **Mouth Synchronisation:** Animated mouth on the ESP32 display synchronised with the volume (dB level) of Gemini's speech.
* Custom-trained sentence-to-emotion classifier running on the Raspberry Pi.
* Tightly integrated hardware design with minimal external/USB peripherals.

## 3. Technology Stack

* **Cloud AI Service:** Google Gemini API (e.g., `gemini-2.5-flash-preview-native-audio-dialog`).
* **Primary Application Logic (Raspberry Pi):** Python 3.
* **Display & Low-Level Control (ESP32):** C/C++ (Arduino IDE or ESP-IDF).
* **Emotion Classification Model:** Custom-trained text classifier (e.g., Scikit-learn, TensorFlow Lite) deployed on Raspberry Pi.
* **Key Python Libraries (Raspberry Pi):**
    * `google-generativeai`
    * `pyserial` or RPi.GPIO for UART communication
    * ALSA utilities / `sounddevice` / `PyAudio` (for I2S mic input & audio analysis)
    * Machine learning libraries for emotion model inference (e.g., `scikit-learn`, `tensorflow-lite-runtime`)
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
    * Analysing its own audio output (Gemini's voice) for dB levels (for mouth sync).
    * Sending high-level display commands (emotion, mouth level) to the ESP32.
    * Handling button input (either directly via GPIO or via ESP32).
* **Integrated Peripherals:**
    * **Microphone Input:** I2S Digital Microphone module (e.g., INMP441) via GPIO.
    * **Speaker Output:** I2S DAC & Amplifier module (e.g., MAX98357A) via GPIO, driving an internal speaker.
    * **Camera:** Raspberry Pi Camera Module (via CSI port).

### B. ESP32 with Integrated Display (The Face & Input Handler)

* **Model:** ESP32 module with a built-in colour TFT/OLED display (and sufficient PSRAM if animations are complex).
* **Responsibilities:**
    * Receiving display commands from the Raspberry Pi.
    * Rendering and animating the robot's face (eyes, mouth, emotion indicators) on its display.
    * Animating the mouth based on dB levels received from the Pi.
    * (Potentially) Reading a button press and sending it to the Pi if the button is physically part of the ESP32 assembly.
* **Connected Peripherals:**
    * The integrated display itself.
    * Tactile button (if hosted by the ESP32).

### C. Supporting Components

* **Speaker:** Compact speaker matched to the Raspberry Pi's I2S DAC/Amp.
* **Chassis:** Custom 3D Printed enclosure.
* **Power Supply:** Stable 5V, 3A+ power source for the Raspberry Pi, with power distributed to the ESP32 module.

## 5. Integration Points & Communication Protocols

* **Raspberry Pi <-> Google Gemini API:** Secure HTTPS.
* **Raspberry Pi (Audio Input):** I2S Mic -> Pi GPIO.
* **Raspberry Pi (Audio Output for Playback & Analysis):** Pi GPIO -> I2S DAC -> Speaker. (Python script analyses this stream before/during playback).
* **Raspberry Pi <-> ESP32:**
    * **Physical Link:** Serial (UART) connection (Pi GPIO TX/RX <-> ESP32 RX/TX). Logic level shifting if voltages differ.
    * **Protocol:** Custom serial messages (e.g., JSON strings or simple delimited commands like `"FACE:HAPPY"`, `"MOUTH:0.75"`, `"EVENT:BUTTON_PRESS"`).

## 6. Development Strategy & Phased Rollout

* **Phase 1: Core Software (Laptop Development):**
    * **Gemini Interaction Module (Python):** Develop and test Gemini communication, audio I/O (using laptop mic/speakers), and text response capture.
    * **Sentence-to-Emotion Classifier (Python):**
        * Generate sentence-emotion dataset using an LLM.
        * Train, evaluate, and save the classification model.
        * Create an inference function.
    * **Audio Analysis for Mouth Sync (Python):** Develop logic to derive dB levels from audio being played.
    * **Simulated ESP32 Face Display (Python GUI or C/C++ Window on Laptop):** Create a window to visualise facial expressions and mouth movements based on commands.
    * **Main Orchestration Script (Python):** Integrate all above modules on the laptop.

* **Phase 2: Raspberry Pi Integration:**
    * Port Python application to Raspberry Pi.
    * Integrate I2S microphone for audio input.
    * Integrate I2S DAC/Speaker for audio output and dB analysis.
    * Test the emotion classifier and mouth sync logic on the Pi.

* **Phase 3: ESP32 Display Firmware & Communication:**
    * Develop ESP32 firmware to:
        * Initialise and control its display.
        * Render different facial expressions (assets or drawn).
        * Animate the mouth based on received levels.
        * Handle button input (if applicable).
        * Receive and parse commands from the Raspberry Pi via serial.
    * Establish and test robust serial communication between Pi and ESP32.

* **Phase 4: Full System Assembly & Testing:**
    * Assemble all components into the 3D printed chassis.
    * End-to-end testing: Button press -> Pi & Gemini interaction -> Emotion classification -> Face display on ESP32 with synchronised mouth.
    * Refine timings, animations, and overall responsiveness.

## 7. Success Criteria / Desired Outcomes

* Robot initiates conversation and responds coherently via Gemini.
* ESP32 display clearly shows distinct facial expressions corresponding to the classified emotion of Gemini's responses.
* Animated mouth on the ESP32 display moves in reasonable sync with Gemini's voice output.
* Interaction latency is acceptable for a conversational experience.
* Hardware is neatly integrated into the final chassis.
* The custom emotion classifier performs with satisfactory accuracy.

## 8. Potential Challenges & Risks

* **Gemini API Free Tier Limits:** Especially RPD for relevant models.
* **Emotion Classifier Accuracy & Nuance:** Achieving good performance that feels natural.
* **I2S Configuration on Pi:** Can be complex for both input and output.
* **Real-time Performance on Pi:** Balancing AI processing, audio analysis, and communication.
* **Pi-ESP32 Serial Communication:** Ensuring robustness and speed.
* **Power Management:** Stable power for all components.
* **Latency:** Cumulative latency from all processing steps.

