# JARVIS AI - Personal Desktop Assistant

JARVIS AI is a cloud-powered personal desktop AI assistant built with Python, PySide6, and Google's Gemini API. Inspired by the iconic Iron Man AI, JARVIS combines advanced generative AI capabilities with a dark glassmorphic ("Liquid Glass") UI, animated AI core visualization, and task & memory management features.

---

## ✨ Features

- **Liquid Glass Interface**: High-tech translucent visual aesthetic with custom shaders and fluid layout transitions built natively on Qt/PySide6.
- **Animated AI Core**: Dynamic Arc Reactor core visualization that reflects real-time AI states (*Idle*, *Thinking*, *Speaking*, *Error*).
- **Google Gemini Integration**: Asynchronous integration with Google Gemini generative models (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-pro`).
- **Task Management**: Interactive task list interface to manage and persist to-dos and priorities.
- **Memory & Personalization**: Store persistent facts and user preferences that are automatically injected into the AI context for tailored responses.
- **Secure Key Storage**: Safe storage of your Gemini API credentials via the OS Keyring / Credential Manager.
- **Non-blocking Operations**: Powered by `qasync` and `asyncio.to_thread` to guarantee 60 FPS UI responsiveness during heavy background network calls.
- **Modular Navigation**: Dedicated views for Chat, Email, Windows Automation, Task Management, Memory & Context, and Application Settings.

---

## 🛠️ Architecture Overview

```
JARVIS_AI/
├── main.py                  # Application entry point with qasync event loop integration
├── Jarvis_UI.py             # Main window layout, sidebar navigation, task/memory managers, and chat handling
├── gemini_api.py            # Gemini API provider wrapper, memory context injection, and session manager
├── ai_core_visualization.py # Animated Arc Reactor AI Core widget
├── gui_components.py        # Liquid Glass UI card and background widgets
├── config.py                # Configuration persistence and secure credential manager
├── utils.py                 # Logging setups and user message dialogs
└── requirements.txt         # Project dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Google Gemini API Key**: Obtain a key from [Google AI Studio](https://aistudio.google.com/).

### Installation & Virtual Environment Setup

1. **Clone or Navigate to the Repository**:
   ```bash
   git clone https://github.com/your-username/JARVIS_AI.git
   cd JARVIS_AI
   ```

2. **Create the Virtual Environment**:
   > ⚠️ **Important**: You must create the virtual environment before trying to activate it!
   ```bash
   python -m venv venv
   ```

3. **Activate Virtual Environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     *If PowerShell displays an `ExecutionPolicy` error, run this first:*
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
     .\venv\Scripts\Activate.ps1
     ```

   - **Windows (Command Prompt / CMD)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```

   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

4. **Install Required Packages (Fixes `ModuleNotFoundError: No module named 'PySide6'`)**:
   > ⚠️ **Crucial**: While your virtual environment `(venv)` is active, you **must** run `pip install -r requirements.txt` to install `PySide6` and all required libraries!
   ```bash
   pip install -r requirements.txt
   ```

5. **Launch Application**:
   ```bash
   python main.py
   ```

---

## ⚙️ Configuration

1. Launch JARVIS AI and navigate to the **Settings** section (⚙️) on the left sidebar.
2. Enter your **Google Gemini API Key**.
3. Select your desired model (e.g., `gemini-1.5-flash` or `gemini-2.0-flash`).
4. Click **Save & Validate Credentials**. Your API key will be securely saved into your operating system's credential manager.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
