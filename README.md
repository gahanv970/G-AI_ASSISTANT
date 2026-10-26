# JARVIS AI - Personal AI Desktop Assistant

JARVIS AI is a cloud-powered personal AI assistant for Windows, inspired by the futuristic assistant concept from Iron Man. This application combines a powerful conversational AI brain with a futuristic animated desktop GUI, aiming to provide intelligent assistance and desktop automation.

## Project Status: Phase 2 - Gemini Text Chat Implemented

This release includes:
*   A functional "Liquid Glass" PySide6 desktop GUI.
*   An animated JARVIS AI core visualization with state indicators (Idle, Thinking).
*   A text-based chat interface for interacting with JARVIS.
*   Integration with the Google Gemini API for conversational AI.
*   Secure storage of your Gemini API key using Windows Credential Manager.
*   A settings screen to enter and test your Gemini API key and select the AI model.
*   Asynchronous operations to keep the UI responsive during AI requests.

## Setup and Installation

### 1. Prerequisites

*   **Python 3.11+**: Download and install from [python.org](https://www.python.org/downloads/). Ensure you add Python to your PATH during installation.
*   **Google Gemini API Key**:
    1.  Go to [Google AI Studio](https://aistudio.google.com/).
    2.  Sign in with your Google account.
    3.  Create a new project or select an existing one.
    4.  Generate an API key. **Keep this key secure and do not share it.**

### 2. Clone the Repository (or create files manually)

If you have the project files, navigate to the project directory. If you are building from scratch, create a directory named `JARVIS_AI` and place the generated files (`main.py`, `jarvis_ui.py`, `gui_components.py`, `ai_core_visualization.py`, `gemini_api.py`, `config.py`, `utils.py`, `requirements.txt`, `README.md`, `pyinstaller_config.spec`) inside it.

### 3. Set up a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

```bash
cd JARVIS_AI
python -m venv venv
.\venv\Scripts\activate  # On Windows
# source venv/bin/activate # On Linux/macOS (if you're adapting for other OS)