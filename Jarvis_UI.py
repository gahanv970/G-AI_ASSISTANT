# JARVIS_AI/jarvis_ui.py
import asyncio
import html
import logging
 
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot
 
from ai_core_visualization import AICoreVisualization
from config import load_config
from gemini_api import GeminiAIProvider
from gui_components import LiquidGlassBackground, LiquidGlassCard
from utils import show_error_message, show_info_message
 
logger = logging.getLogger(__name__)
 
MASKED_KEY = "********"
DEFAULT_MODEL = "gemini-pro"
 
 
class JarvisMainWindow(QMainWindow):
    """
    The main window for the JARVIS AI desktop assistant, featuring a Liquid Glass UI.
 
    Blocking calls (Gemini requests) are pushed to a worker thread with
    asyncio.to_thread() and awaited from qasync-powered slots, so the UI never
    freezes and no QThread lifetime management is needed.
    """
 
    ai_state_changed = Signal(str)  # Updates the AI core visualization state
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS AI")
        self.resize(1200, 800)
        self.setMinimumSize(1024, 768)
 
        self.ai_provider = GeminiAIProvider()
        self.conversation_history = []  # list of (role, text) tuples, role in {"User", "JARVIS"}
        self._busy = False
 
        # One shared timer for "return to idle" so overlapping requests can't
        # reset the visualization while a new request is still running.
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(lambda: self.ai_state_changed.emit("idle"))
 
        self._setup_ui()
        self._setup_connections()
        self._load_settings()
 
        self.ai_state_changed.emit("idle")
        logger.info("JARVIS AI application started.")
 
    # ------------------------------------------------------------------ UI setup
 
    def _setup_ui(self):
        """Initializes the Liquid Glass GUI components and layout."""
        self.background_widget = LiquidGlassBackground(self)
        self.setCentralWidget(self.background_widget)
 
        # The layout is installed directly on the background widget.
        self.root_layout = QHBoxLayout(self.background_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
 
        # --- Left sidebar (navigation) ---
        self.sidebar = LiquidGlassCard(self.background_widget, corner_radius=28)
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 30, 15, 15)
        sidebar_layout.setSpacing(10)
 
        for index, label in enumerate(("Chat", "Email", "Automation", "Tasks", "Memory", "Settings")):
            self._add_sidebar_button(label, index)
        sidebar_layout.addStretch()  # Push buttons to top
 
        self.root_layout.addWidget(self.sidebar)
 
        # --- Main content area ---
        self.content_area = QWidget(self.background_widget)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
 
        self.stacked_widget = QStackedWidget(self.content_area)
        self.content_layout.addWidget(self.stacked_widget)
 
        self._setup_chat_view()
        self.stacked_widget.addWidget(self.chat_view)  # 0
 
        self.stacked_widget.addWidget(self._create_placeholder_view("Email Integration (Phase 3)"))  # 1
        self.stacked_widget.addWidget(self._create_placeholder_view("Windows Automation (Phase 5)"))  # 2
        self.stacked_widget.addWidget(self._create_placeholder_view("Task Management (Phase 6)"))  # 3
        self.stacked_widget.addWidget(self._create_placeholder_view("Memory & Personalization (Phase 6)"))  # 4
 
        self._setup_settings_view()
        self.stacked_widget.addWidget(self.settings_view)  # 5
 
        self.root_layout.addWidget(self.content_area, stretch=1)
 
        self.setStyleSheet("""
            QMainWindow {
                background: transparent; /* Handled by LiquidGlassBackground */
            }
            QLabel, QPushButton, QLineEdit, QTextEdit {
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 12px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: rgba(0, 200, 255, 50);
                border: 1px solid rgba(0, 200, 255, 100);
            }
            QPushButton:pressed {
                background-color: rgba(0, 150, 200, 70);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 12);
                color: rgba(224, 224, 224, 90);
            }
            QLineEdit, QTextEdit {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
                padding: 8px;
            }
            QTextEdit {
                padding: 10px;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 10);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 200, 255, 100);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
 
    def _add_sidebar_button(self, text, page_index):
        """Creates a styled sidebar button that switches to the given page."""
        button = QPushButton(text)
        button.setFixedSize(160, 40)
        # Default args bind the index per button; `checked` swallows clicked(bool).
        button.clicked.connect(
            lambda checked=False, i=page_index: self.stacked_widget.setCurrentIndex(i)
        )
        self.sidebar.layout().addWidget(button)
 
    def _create_placeholder_view(self, text, parent=None):
        """Creates a simple placeholder view for unimplemented sections."""
        view = LiquidGlassCard(parent or self.content_area, corner_radius=32)
        layout = QVBoxLayout(view)
        label = QLabel(f"<h2>{text}</h2><p><i>Coming in future phases...</i></p>")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #99CCFF;")
        layout.addWidget(label)
        return view
 
    def _setup_chat_view(self):
        """Sets up the main chat interface with AI core visualization."""
        self.chat_view = QWidget(self.content_area)
        chat_layout = QVBoxLayout(self.chat_view)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(15)
 
        # Top section: AI core visualization and status
        top_panel = QWidget(self.chat_view)
        top_panel_layout = QHBoxLayout(top_panel)
        top_panel_layout.setContentsMargins(0, 0, 0, 0)
        top_panel_layout.setSpacing(20)
 
        self.ai_core_viz = AICoreVisualization(self.chat_view)
        self.ai_core_viz.setFixedSize(250, 250)
        top_panel_layout.addWidget(self.ai_core_viz, alignment=Qt.AlignCenter)
        self.ai_state_changed.connect(self.ai_core_viz.set_state)
 
        status_card = LiquidGlassCard(self.chat_view, corner_radius=28)
        status_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        status_layout = QVBoxLayout(status_card)
        status_layout.addWidget(QLabel("<h3>System Status</h3>"))
        self.ai_status_label = QLabel("AI: Idle")
        self.gmail_status_label = QLabel("Gmail: Disconnected")
        status_layout.addWidget(self.ai_status_label)
        status_layout.addWidget(self.gmail_status_label)
        status_layout.addStretch()
        top_panel_layout.addWidget(status_card)
 
        chat_layout.addWidget(top_panel)
 
        # Conversation area
        self.conversation_display = QTextEdit(self.chat_view)
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setPlaceholderText("JARVIS: How may I assist you?")
        self.conversation_display.setFont(QFont("Segoe UI", 10))
        chat_layout.addWidget(self.conversation_display, stretch=1)
 
        # Command input
        input_panel = QWidget(self.chat_view)
        input_layout = QHBoxLayout(input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
 
        self.command_input = QLineEdit(self.chat_view)
        self.command_input.setPlaceholderText("Type your command here...")
        self.command_input.setFont(QFont("Segoe UI", 10))
        self.command_input.returnPressed.connect(self._send_command)
        input_layout.addWidget(self.command_input)
 
        self.microphone_button = QPushButton("🎙️")
        self.microphone_button.setFixedSize(40, 40)
        self.microphone_button.clicked.connect(self._toggle_microphone)
        input_layout.addWidget(self.microphone_button)
 
        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(80, 40)
        self.send_button.clicked.connect(self._send_command)
        input_layout.addWidget(self.send_button)
 
        chat_layout.addWidget(input_panel)
 
    def _setup_settings_view(self):
        """Sets up the settings interface for API keys and other configurations."""
        self.settings_view = QWidget(self.content_area)
        settings_layout = QVBoxLayout(self.settings_view)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(15)
 
        scroll_area = QScrollArea(self.settings_view)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        scroll_area.setWidget(scroll_content)
        settings_layout.addWidget(scroll_area)
 
        # Gemini API settings card
        gemini_card = LiquidGlassCard(scroll_content, corner_radius=28)
        gemini_layout = QVBoxLayout(gemini_card)
        scroll_layout.addWidget(gemini_card)
 
        gemini_layout.addWidget(QLabel("<h3>Gemini API Configuration</h3>"))
        gemini_layout.addWidget(QLabel("Enter your Google Gemini API Key:"))
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.Password)
        gemini_layout.addWidget(self.gemini_api_key_input)
 
        self.save_key_button = QPushButton("Save & Test Gemini Key")
        self.save_key_button.clicked.connect(self._save_and_test_gemini_key)
        gemini_layout.addWidget(self.save_key_button)
 
        gemini_layout.addWidget(QLabel("Select Gemini Model:"))
        self.gemini_model_selector = QLineEdit()
        self.gemini_model_selector.setPlaceholderText("e.g., gemini-pro")
        gemini_layout.addWidget(self.gemini_model_selector)
 
        # Placeholders for other settings
        for title in (
            "Gmail Settings (Phase 3)",
            "Voice Settings (Phase 4)",
            "PC Automation Permissions (Phase 5)",
            "Memory & Data Retention (Phase 6)",
        ):
            scroll_layout.addWidget(self._create_placeholder_view(title, parent=scroll_content))
 
        scroll_layout.addStretch()
 
    def _setup_connections(self):
        """Connects signals and slots that aren't wired up during widget creation."""
        pass
 
    # ------------------------------------------------------------------ Settings
 
    def _load_settings(self):
        """Loads settings from config.py and secure storage."""
        app_config = load_config()
        self.gemini_model_selector.setText(app_config.get("gemini_model", DEFAULT_MODEL))
 
        try:
            stored_key = self.ai_provider.get_api_key_securely()
            if stored_key:
                self.gemini_api_key_input.setText(MASKED_KEY)
                self.ai_provider.set_api_key(stored_key)
                logger.info("Gemini API key loaded from secure storage.")
                self.ai_status_label.setText("AI: Ready (Key Loaded)")
            else:
                logger.warning("No Gemini API key found in secure storage.")
                self.ai_status_label.setText("AI: Not Configured")
        except Exception as e:
            logger.error(f"Failed to load Gemini API key from secure storage: {e}")
            self.ai_status_label.setText("AI: Config Error")
            show_error_message(
                "Security Error",
                f"Could not retrieve Gemini API key: {e}. Please check your system's credential manager.",
            )
 
    def _current_model_name(self):
        """Read the model name (must be called from the GUI thread)."""
        return self.gemini_model_selector.text().strip() or DEFAULT_MODEL
 
    @asyncSlot()
    async def _save_and_test_gemini_key(self):
        """Saves the Gemini API key securely and performs a test API call."""
        api_key = self.gemini_api_key_input.text().strip()
        if api_key == MASKED_KEY:
            show_info_message(
                "Key Already Set",
                "Gemini API key is already securely stored. If you wish to change it, please enter the new key.",
            )
            return
        if not api_key:
            show_error_message("Input Error", "Gemini API Key cannot be empty.")
            return
 
        model_name = self._current_model_name()
 
        try:
            self.ai_provider.save_api_key_securely(api_key)
            self.ai_provider.set_api_key(api_key)  # Use for the current session
            logger.info("Gemini API key saved securely.")
        except Exception as e:
            logger.exception("Failed to save Gemini API key.")
            show_error_message("Error", f"Failed to save Gemini API key: {e}")
            self.ai_status_label.setText("AI: Config Error")
            return
 
        self.gemini_api_key_input.setText(MASKED_KEY)
        self.ai_status_label.setText("AI: Testing...")
        self.ai_state_changed.emit("thinking")
        self.save_key_button.setEnabled(False)
 
        try:
            # Blocking network call runs in a worker thread; the UI stays responsive.
            ok = await asyncio.to_thread(self.ai_provider.test_connection, model_name)
        except Exception as e:
            logger.exception("Gemini API test failed.")
            self._handle_gemini_test_error(str(e))
        else:
            self._handle_gemini_test_result(ok)
        finally:
            self.save_key_button.setEnabled(True)
 
    def _handle_gemini_test_result(self, result):
        """Handles the result of the Gemini API key test."""
        if result:
            show_info_message("Gemini API Test", "Gemini API key is valid and connection successful!")
            self.ai_status_label.setText("AI: Ready")
        else:
            show_error_message(
                "Gemini API Test Failed",
                "Gemini API key is invalid or connection failed. Check your key and network.",
            )
            self.ai_status_label.setText("AI: Invalid Key")
        self.ai_state_changed.emit("idle")
 
    def _handle_gemini_test_error(self, error_msg):
        """Handles errors during the Gemini API key test."""
        show_error_message("Gemini API Test Error", f"An error occurred during API test: {error_msg}")
        self.ai_status_label.setText("AI: Test Error")
        self.ai_state_changed.emit("idle")
 
    # ------------------------------------------------------------------ Chat
 
    @asyncSlot()
    async def _send_command(self):
        """Handles sending a text command to JARVIS."""
        if self._busy:
            return
 
        user_text = self.command_input.text().strip()
        if not user_text:
            return
 
        if not self.ai_provider.is_configured():
            show_error_message("AI Not Configured", "Gemini API key not configured. Please set it in Settings.")
            return
 
        model_name = self._current_model_name()
 
        self.command_input.clear()
        self._append_message("User", user_text)
        history = self._build_gemini_history()
 
        self._set_busy(True)
        self._idle_timer.stop()
        self.ai_state_changed.emit("thinking")
        self.ai_status_label.setText("AI: Thinking...")
 
        try:
            response_text = await asyncio.to_thread(self.ai_provider.send_message, history, model_name)
        except Exception as e:
            logger.exception("Gemini request failed.")
            self._handle_gemini_error(str(e))
        else:
            self._handle_gemini_response(response_text)
        finally:
            self._set_busy(False)
 
    def _build_gemini_history(self):
        """
        Converts conversation_history into Gemini's format:
        [{'role': 'user' | 'model', 'parts': [text]}, ...]
        The latest user message is already in conversation_history.
        """
        return [
            {"role": "user" if role == "User" else "model", "parts": [text]}
            for role, text in self.conversation_history
        ]
 
    def _set_busy(self, busy):
        """Locks/unlocks the input controls while a request is in flight."""
        self._busy = busy
        self.send_button.setEnabled(not busy)
        self.command_input.setEnabled(not busy)
        if not busy:
            self.command_input.setFocus()
 
    def _handle_gemini_response(self, response_text):
        """Handles the response from Gemini and updates the UI."""
        self._append_message("JARVIS", response_text)
        self.ai_state_changed.emit("speaking")  # Visual only; TTS comes in a later phase
        self.ai_status_label.setText("AI: Ready")
        self._idle_timer.start(2000)
 
    def _handle_gemini_error(self, error_msg):
        """Handles errors during the Gemini API call."""
        # Don't keep the unanswered user message, or the next request would
        # send two consecutive "user" turns.
        if self.conversation_history and self.conversation_history[-1][0] == "User":
            self.conversation_history.pop()
 
        self._append_message("JARVIS (Error)", f"I encountered an issue: {error_msg}", store=False)
        show_error_message("AI Error", f"JARVIS encountered an error: {error_msg}")
        self.ai_state_changed.emit("error")
        self.ai_status_label.setText("AI: Error")
        self._idle_timer.start(5000)
 
    def _append_message(self, sender, text, store=True):
        """Adds a message to the history (optionally) and to the conversation display."""
        if store:
            self.conversation_history.append((sender, text))
 
        colors = {"User": "#99CCFF", "JARVIS": "#7FFFD4", "JARVIS (Error)": "#FF8080"}
        color = colors.get(sender, "#E0E0E0")
        safe_text = html.escape(str(text)).replace("\n", "<br>")
        self.conversation_display.append(
            f'<p><b style="color:{color};">{html.escape(sender)}:</b> {safe_text}</p>'
        )
        bar = self.conversation_display.verticalScrollBar()
        bar.setValue(bar.maximum())
 
    def _toggle_microphone(self):
        """Placeholder until voice input is implemented (Phase 4)."""
        show_info_message("Voice Input", "Voice input will be available in Phase 4.")