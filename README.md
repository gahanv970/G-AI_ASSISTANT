# JARVIS AI - Personal Desktop Assistant

JARVIS AI is a cloud-powered personal desktop AI assistant built with Python, PySide6, and Google's Gemini API. Inspired by the iconic Iron Man AI, JARVIS combines advanced generative AI capabilities with a dark glassmorphic ("Liquid Glass") UI, desktop automation, email management, task tracking, long-term memory, and an animated AI core visualization.

---

## ✨ Features

- **Liquid Glass Interface**: High-tech translucent visual aesthetic with custom shaders and fluid layout transitions built natively on Qt/PySide6.
- **Animated AI Core**: Dynamic Arc Reactor core visualization that reflects real-time AI states (*Idle*, *Thinking*, *Speaking*, *Error*).
- **Google Gemini Integration**: Asynchronous integration with Google Gemini generative models (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-pro`).
- **Desktop Automation & Computer Control**: Launch local desktop applications immediately or with a delayed timer (e.g. `"open calculator"`, `"open notepad in 5 seconds"`), open web pages, and automatically view weather forecasts (`"watch the weather tomorrow"`).
- **Email Automation**: Compose and dispatch emails with SMTP support or logged history directly from the UI or natural language chat (`"email user@domain.com saying hi"`).
- **Task & Goal Management**: Organize pending and completed tasks, assign priority levels, and filter daily task lists.
- **Memory & Context Bank**: Save key user preferences, facts, and instructions to long-term memory so JARVIS retains context across sessions.
- **Secure Key Storage**: Safe storage of your Gemini API credentials via OS Keyring with local fallback support.
- **Non-blocking Operations**: Powered by `qasync` and `asyncio.to_thread` to guarantee 60 FPS UI responsiveness.

---

## 🛠️ Architecture Overview

```
JARVIS_AI/
├── main.py                  # Application entry point with qasync event loop integration
├── Jarvis_UI.py             # Main window layout, sidebar navigation, and interactive views
├── automation_engine.py     # OS desktop launcher, delayed timer, web navigation, and email engine
├── memory_manager.py        # Long-term memory storage and AI prompt context builder
├── task_manager.py          # Task and goal tracking store
├── gemini_api.py            # Gemini API provider wrapper and session manager
├── ai_core_visualization.py # Animated Arc Reactor AI Core widget
├── gui_components.py        # Liquid Glass UI card and background widgets
├── config.py                # Configuration and secure credential manager
├── utils.py                 # Logging setups and user message dialogs
└── requirements.txt         # Project dependencies (PySide6, qasync, google-generativeai, keyring, etc.)
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
   python3 -m venv venv

   # On Windows:
   .\venv\Scripts\activate

   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   Ensure you install all required packages into your activated virtual environment:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Installing `requirements.txt` installs `PySide6`, `qasync`, `google-generativeai`, `keyring`, and `requests`.*

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

## 🧪 Running Tests

To run the test suite headlessly:
```bash
QT_QPA_PLATFORM=offscreen python -m pytest
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
