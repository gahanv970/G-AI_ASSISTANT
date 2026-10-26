# JARVIS AI - Personal Desktop Assistant

JARVIS AI is a cloud-powered personal desktop AI assistant built with Python, PySide6, and Google's Gemini API. Inspired by the iconic Iron Man AI, JARVIS combines advanced generative AI capabilities with a dark glassmorphic ("Liquid Glass") UI and animated AI core visualization.

---

## ✨ Features

- **Liquid Glass Interface**: High-tech translucent visual aesthetic with custom shaders and fluid layout transitions built natively on Qt/PySide6.
- **Animated AI Core**: Dynamic Arc Reactor core visualization that reflects real-time AI states (*Idle*, *Thinking*, *Speaking*, *Error*).
- **Google Gemini Integration**: Asynchronous integration with Google Gemini generative models (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-pro`).
- **Secure Key Storage**: Safe storage of your Gemini API credentials via the OS Keyring / Credential Manager.
- **Non-blocking Operations**: Powered by `qasync` and `asyncio.to_thread` to guarantee 60 FPS UI responsiveness during heavy background network calls.
- **Modular Navigation**: Dedicated views for Chat, Email, Windows Automation, Task Management, Memory & Context, and Application Settings.

---

## 🛠️ Architecture Overview

```
JARVIS_AI/
├── main.py                  # Application entry point with qasync event loop integration
├── Jarvis_UI.py             # Main window layout, sidebar navigation, and chat handling
├── gemini_api.py            # Gemini API provider wrapper and session manager
├── ai_core_visualization.py # Animated Arc Reactor AI Core widget
├── gui_components.py        # Liquid Glass UI card and background widgets
├── config.py                # Configuration and secure credential manager
├── utils.py                 # Logging setups and user message dialogs
└── requirements.txt         # Project dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Google Gemini API Key**: Obtain a key from [Google AI Studio](https://aistudio.google.com/).

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/JARVIS_AI.git
   cd JARVIS_AI
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch Application**:
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
