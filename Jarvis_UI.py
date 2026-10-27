import asyncio
import html
import logging

from PySide6.QtCore import Qt, QTimer, Signal, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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
from config import load_config, save_config
from gemini_api import GeminiAIProvider
from gui_components import LiquidGlassBackground, LiquidGlassCard
from utils import show_error_message, show_info_message

logger = logging.getLogger(__name__)

MASKED_KEY = "********"
DEFAULT_MODEL = "gemini-1.5-flash"


class JarvisMainWindow(QMainWindow):
    """
    The main window for the JARVIS AI desktop assistant, featuring a Liquid Glass UI.
    """

    ai_state_changed = Signal(str)  # Updates the AI core visualization state

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS AI Assistant")
        self.resize(1200, 800)
        self.setMinimumSize(1024, 768)

        self.ai_provider = GeminiAIProvider()
        self.conversation_history = []  # list of (role, text) tuples
        self.all_tasks = []  # list of task dicts
        self._busy = False
        self._sidebar_buttons = []

        # Timer to reset core visualization state back to idle
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(lambda: self.ai_state_changed.emit("idle"))

        self._setup_ui()
        self._load_settings()
        self._load_tasks_and_memories()

        self.ai_state_changed.emit("idle")
        logger.info("JARVIS AI application initialized successfully.")

    # ------------------------------------------------------------------ UI Setup

    def _setup_ui(self):
        """Initializes the Liquid Glass GUI components and layout."""
        self.background_widget = LiquidGlassBackground(self)
        self.setCentralWidget(self.background_widget)

        self.root_layout = QHBoxLayout(self.background_widget)
        self.root_layout.setContentsMargins(15, 15, 15, 15)
        self.root_layout.setSpacing(15)

        # --- Left sidebar (navigation) ---
        self.sidebar = LiquidGlassCard(self.background_widget, corner_radius=24)
        self.sidebar.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 24, 12, 18)
        sidebar_layout.setSpacing(10)

        # App Title in Sidebar
        app_title = QLabel("JARVIS AI")
        app_title.setAlignment(Qt.AlignCenter)
        app_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        app_title.setStyleSheet("color: #00C8FF; margin-bottom: 15px;")
        sidebar_layout.addWidget(app_title)

        nav_items = [
            ("💬 Chat", 0),
            ("📧 Email", 1),
            ("⚡ Automation", 2),
            ("📋 Tasks", 3),
            ("🧠 Memory", 4),
            ("⚙️ Settings", 5),
        ]

        for text, index in nav_items:
            btn = self._add_sidebar_button(text, index)
            self._sidebar_buttons.append(btn)

        sidebar_layout.addStretch()

        self.root_layout.addWidget(self.sidebar)

        # --- Main content area ---
        self.content_area = QWidget(self.background_widget)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget(self.content_area)
        self.content_layout.addWidget(self.stacked_widget)

        self._setup_chat_view()
        self.stacked_widget.addWidget(self.chat_view)  # 0

        self.stacked_widget.addWidget(self._create_placeholder_view(
            "Email Integration", "Manage and compose emails using Gemini AI."))  # 1
        self.stacked_widget.addWidget(self._create_placeholder_view(
            "Windows Automation", "Control apps, automate tasks, and run desktop workflows."))  # 2

        self._setup_tasks_view()
        self.stacked_widget.addWidget(self.tasks_view)  # 3

        self._setup_memory_view()
        self.stacked_widget.addWidget(self.memory_view)  # 4

        self._setup_settings_view()
        self.stacked_widget.addWidget(self.settings_view)  # 5

        self.stacked_widget.currentChanged.connect(self._on_page_changed)
        self.root_layout.addWidget(self.content_area, stretch=1)

        # Set initial active tab
        self._update_sidebar_styles(0)

        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
            }
            QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QComboBox, QDateEdit {
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 10px;
                padding: 8px 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(0, 200, 255, 40);
                border: 1px solid rgba(0, 200, 255, 120);
            }
            QPushButton:pressed {
                background-color: rgba(0, 150, 200, 70);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 10);
                color: rgba(224, 224, 224, 80);
                border: 1px solid rgba(255, 255, 255, 15);
            }
            QLineEdit, QTextEdit, QListWidget, QComboBox, QDateEdit {
                background-color: rgba(15, 23, 42, 180);
                border: 1px solid rgba(0, 200, 255, 60);
                border-radius: 10px;
                padding: 8px 12px;
                selection-background-color: #00C8FF;
                selection-color: #000000;
            }
            QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid rgba(0, 200, 255, 180);
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 10);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 200, 255, 120);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

    def _add_sidebar_button(self, text, page_index):
        """Creates a styled sidebar navigation button."""
        button = QPushButton(text)
        button.setFixedHeight(42)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(page_index))
        self.sidebar.layout().addWidget(button)
        return button

    def _on_page_changed(self, index):
        """Updates active sidebar button styling on page change."""
        self._update_sidebar_styles(index)

    def _update_sidebar_styles(self, active_index):
        """Highlights the active sidebar navigation tab."""
        for i, btn in enumerate(self._sidebar_buttons):
            if i == active_index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(0, 200, 255, 70);
                        border: 1px solid rgba(0, 200, 255, 180);
                        color: #FFFFFF;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("")

    def _create_placeholder_view(self, title, description):
        """Creates a placeholder card for upcoming features."""
        view = LiquidGlassCard(self.content_area, corner_radius=24)
        layout = QVBoxLayout(view)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        label_title = QLabel(f"<h2 style='color: #00C8FF;'>{title}</h2>")
        label_title.setAlignment(Qt.AlignCenter)
        label_desc = QLabel(f"<p style='color: #A0AEC0; font-size: 14px;'>{description}</p>")
        label_desc.setAlignment(Qt.AlignCenter)
        label_status = QLabel("<p style='color: #718096; font-style: italic;'>Feature under active development</p>")
        label_status.setAlignment(Qt.AlignCenter)

        layout.addWidget(label_title)
        layout.addWidget(label_desc)
        layout.addWidget(label_status)
        return view

    def _setup_chat_view(self):
        """Sets up the main interactive chat interface."""
        self.chat_view = QWidget(self.content_area)
        chat_layout = QVBoxLayout(self.chat_view)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(15)

        # Top section: Core animation & status card
        top_panel = QWidget(self.chat_view)
        top_panel_layout = QHBoxLayout(top_panel)
        top_panel_layout.setContentsMargins(0, 0, 0, 0)
        top_panel_layout.setSpacing(15)

        self.ai_core_viz = AICoreVisualization(self.chat_view)
        self.ai_core_viz.setFixedSize(220, 220)
        top_panel_layout.addWidget(self.ai_core_viz, alignment=Qt.AlignCenter)
        self.ai_state_changed.connect(self.ai_core_viz.set_state)

        status_card = LiquidGlassCard(self.chat_view, corner_radius=24)
        status_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(20, 15, 20, 15)

        status_header = QLabel("<h3 style='color: #00C8FF; margin: 0;'>System Overview</h3>")
        status_layout.addWidget(status_header)

        self.ai_status_label = QLabel("AI Engine: Initializing...")
        self.ai_status_label.setFont(QFont("Segoe UI", 10))
        self.model_status_label = QLabel(f"Active Model: {DEFAULT_MODEL}")
        self.model_status_label.setFont(QFont("Segoe UI", 10))

        status_layout.addWidget(self.ai_status_label)
        status_layout.addWidget(self.model_status_label)

        # Clear chat history button in status card
        self.clear_chat_button = QPushButton("Clear Chat History")
        self.clear_chat_button.setFixedHeight(32)
        self.clear_chat_button.setCursor(Qt.PointingHandCursor)
        self.clear_chat_button.clicked.connect(self._clear_chat_history)
        status_layout.addWidget(self.clear_chat_button)

        status_layout.addStretch()

        top_panel_layout.addWidget(status_card)
        chat_layout.addWidget(top_panel)

        # Conversation display widget
        self.conversation_display = QTextEdit(self.chat_view)
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setFont(QFont("Segoe UI", 10))
        self.conversation_display.setPlaceholderText("JARVIS is ready. Ask me anything!")
        chat_layout.addWidget(self.conversation_display, stretch=1)

        # Command input row
        input_panel = QWidget(self.chat_view)
        input_layout = QHBoxLayout(input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)

        self.command_input = QLineEdit(self.chat_view)
        self.command_input.setPlaceholderText("Ask JARVIS or type a command...")
        self.command_input.setFont(QFont("Segoe UI", 10))
        self.command_input.setFixedHeight(42)
        self.command_input.returnPressed.connect(self._send_command)
        input_layout.addWidget(self.command_input)

        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(90, 42)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self._send_command)
        input_layout.addWidget(self.send_button)

        chat_layout.addWidget(input_panel)

    def _setup_tasks_view(self):
        """Sets up the Task Management view with priority, due date, status, and filtering."""
        self.tasks_view = LiquidGlassCard(self.content_area, corner_radius=24)
        layout = QVBoxLayout(self.tasks_view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h2 style='color: #00C8FF;'>Task Management</h2>"))
        header_layout.addStretch()

        header_layout.addWidget(QLabel("Filter:"))
        self.task_filter_combo = QComboBox()
        self.task_filter_combo.addItems(["All", "Active", "Completed"])
        self.task_filter_combo.currentTextChanged.connect(self._render_tasks)
        header_layout.addWidget(self.task_filter_combo)

        layout.addLayout(header_layout)

        # Task creation controls
        input_row = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Task title...")
        self.task_input.setFixedHeight(38)
        self.task_input.returnPressed.connect(self._add_task)
        input_row.addWidget(self.task_input, stretch=2)

        self.task_desc_input = QLineEdit()
        self.task_desc_input.setPlaceholderText("Description (optional)...")
        self.task_desc_input.setFixedHeight(38)
        input_row.addWidget(self.task_desc_input, stretch=2)

        self.task_priority_combo = QComboBox()
        self.task_priority_combo.addItems(["High", "Medium", "Low"])
        self.task_priority_combo.setCurrentText("Medium")
        self.task_priority_combo.setFixedHeight(38)
        input_row.addWidget(self.task_priority_combo)

        self.task_due_date = QDateEdit()
        self.task_due_date.setCalendarPopup(True)
        self.task_due_date.setDate(QDate.currentDate())
        self.task_due_date.setFixedHeight(38)
        input_row.addWidget(self.task_due_date)

        add_btn = QPushButton("Add Task")
        add_btn.setFixedHeight(38)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_task)
        input_row.addWidget(add_btn)

        layout.addLayout(input_row)

        self.tasks_list = QListWidget()
        layout.addWidget(self.tasks_list, stretch=1)

        btn_row = QHBoxLayout()
        toggle_status_btn = QPushButton("Toggle Active/Completed")
        toggle_status_btn.setFixedHeight(36)
        toggle_status_btn.setCursor(Qt.PointingHandCursor)
        toggle_status_btn.clicked.connect(self._toggle_task_status)
        btn_row.addWidget(toggle_status_btn)

        remove_btn = QPushButton("Remove Selected Task")
        remove_btn.setFixedHeight(36)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(self._remove_task)
        btn_row.addWidget(remove_btn)

        layout.addLayout(btn_row)

    def _setup_memory_view(self):
        """Sets up the Memory & Personalization view."""
        self.memory_view = LiquidGlassCard(self.content_area, corner_radius=24)
        layout = QVBoxLayout(self.memory_view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(QLabel("<h2 style='color: #00C8FF;'>Memory & Context</h2>"))

        input_row = QHBoxLayout()
        self.memory_input = QLineEdit()
        self.memory_input.setPlaceholderText(
            "Add a persistent fact or preference (e.g. User prefers concise answers)..."
        )
        self.memory_input.setFixedHeight(38)
        self.memory_input.returnPressed.connect(self._add_memory)
        input_row.addWidget(self.memory_input)

        add_btn = QPushButton("Save Memory")
        add_btn.setFixedHeight(38)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_memory)
        input_row.addWidget(add_btn)

        layout.addLayout(input_row)

        self.memories_list = QListWidget()
        layout.addWidget(self.memories_list, stretch=1)

        btn_row = QHBoxLayout()
        remove_btn = QPushButton("Remove Selected Memory")
        remove_btn.setFixedHeight(36)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(self._remove_memory)
        btn_row.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All Memories")
        clear_btn.setFixedHeight(36)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_memories)
        btn_row.addWidget(clear_btn)

        layout.addLayout(btn_row)

    def _setup_settings_view(self):
        """Sets up configuration settings for API keys and models."""
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

        # Gemini API Config Card
        gemini_card = LiquidGlassCard(scroll_content, corner_radius=24)
        gemini_layout = QVBoxLayout(gemini_card)
        gemini_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.addWidget(gemini_card)

        gemini_layout.addWidget(QLabel("<h3 style='color: #00C8FF;'>Google Gemini API Settings</h3>"))

        gemini_layout.addWidget(QLabel("Gemini API Key:"))
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.Password)
        self.gemini_api_key_input.setPlaceholderText("Enter AI Studio API Key")
        gemini_layout.addWidget(self.gemini_api_key_input)

        gemini_layout.addWidget(QLabel("Select Gemini Model:"))
        self.gemini_model_selector = QLineEdit()
        self.gemini_model_selector.setPlaceholderText("e.g. gemini-1.5-flash, gemini-2.0-flash, gemini-1.5-pro")
        gemini_layout.addWidget(self.gemini_model_selector)

        self.save_key_button = QPushButton("Save & Validate Credentials")
        self.save_key_button.setFixedHeight(40)
        self.save_key_button.setCursor(Qt.PointingHandCursor)
        self.save_key_button.clicked.connect(self._save_and_test_gemini_key)
        gemini_layout.addWidget(self.save_key_button)

        scroll_layout.addStretch()

    # ------------------------------------------------------------------ Tasks & Memory Logic

    def _load_tasks_and_memories(self):
        """Loads tasks and memories from config JSON."""
        config = load_config()
        raw_tasks = config.get("tasks", [])
        self.all_tasks = []

        for item in raw_tasks:
            if isinstance(item, dict):
                self.all_tasks.append(item)
            else:
                self.all_tasks.append({
                    "title": str(item),
                    "description": "",
                    "priority": "Medium",
                    "due_date": QDate.currentDate().toString("yyyy-MM-dd"),
                    "status": "Active"
                })

        self._render_tasks()

        self.memories_list.clear()
        for m in config.get("memories", []):
            self.memories_list.addItem(QListWidgetItem(str(m)))

    def _render_tasks(self):
        """Renders tasks in the QListWidget based on active status filter."""
        self.tasks_list.clear()
        filter_status = self.task_filter_combo.currentText()

        for index, task in enumerate(self.all_tasks):
            status = task.get("status", "Active")
            if filter_status == "Active" and status != "Active":
                continue
            if filter_status == "Completed" and status != "Completed":
                continue

            title = task.get("title", "")
            desc = task.get("description", "")
            priority = task.get("priority", "Medium")
            due = task.get("due_date", "")

            label = f"[{status.upper()}] [{priority} Priority] {title}"
            if due:
                label += f" (Due: {due})"
            if desc:
                label += f" - {desc}"

            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, index)
            self.tasks_list.addItem(item)

    def _save_tasks(self):
        """Saves current tasks to config."""
        config = load_config()
        config["tasks"] = self.all_tasks
        save_config(config)

    def _save_memories(self):
        """Saves current memories to config."""
        memories = [self.memories_list.item(i).text() for i in range(self.memories_list.count())]
        config = load_config()
        config["memories"] = memories
        save_config(config)

    def _add_task(self):
        title = self.task_input.text().strip()
        if title:
            task = {
                "title": title,
                "description": self.task_desc_input.text().strip(),
                "priority": self.task_priority_combo.currentText(),
                "due_date": self.task_due_date.date().toString("yyyy-MM-dd"),
                "status": "Active"
            }
            self.all_tasks.append(task)
            self.task_input.clear()
            self.task_desc_input.clear()
            self._save_tasks()
            self._render_tasks()

    def _toggle_task_status(self):
        item = self.tasks_list.currentItem()
        if item:
            task_idx = item.data(Qt.UserRole)
            if task_idx is not None and 0 <= task_idx < len(self.all_tasks):
                curr = self.all_tasks[task_idx].get("status", "Active")
                self.all_tasks[task_idx]["status"] = "Completed" if curr == "Active" else "Active"
                self._save_tasks()
                self._render_tasks()

    def _remove_task(self):
        item = self.tasks_list.currentItem()
        if item:
            task_idx = item.data(Qt.UserRole)
            if task_idx is not None and 0 <= task_idx < len(self.all_tasks):
                self.all_tasks.pop(task_idx)
                self._save_tasks()
                self._render_tasks()

    def _add_memory(self):
        text = self.memory_input.text().strip()
        if text:
            self.memories_list.addItem(QListWidgetItem(text))
            self.memory_input.clear()
            self._save_memories()

    def _remove_memory(self):
        row = self.memories_list.currentRow()
        if row >= 0:
            self.memories_list.takeItem(row)
            self._save_memories()

    def _clear_memories(self):
        self.memories_list.clear()
        self._save_memories()

    # ------------------------------------------------------------------ Logic & Settings

    def _clear_chat_history(self):
        """Clears the chat history."""
        self.conversation_history.clear()
        self.conversation_display.clear()
        show_info_message("Chat Cleared", "Conversation history has been cleared.")

    def _load_settings(self):
        """Loads non-sensitive config and secure secrets."""
        app_config = load_config()
        model_name = app_config.get("gemini_model", DEFAULT_MODEL)
        self.gemini_model_selector.setText(model_name)
        self.ai_provider.set_model(model_name)
        self.model_status_label.setText(f"Active Model: {model_name}")

        try:
            stored_key = self.ai_provider.get_api_key_securely()
            if stored_key:
                self.gemini_api_key_input.setText(MASKED_KEY)
                self.ai_provider.set_api_key(stored_key)
                logger.info("Gemini API key restored securely.")
                self.ai_status_label.setText("AI Engine: Ready (API Key Loaded)")
            else:
                logger.warning("No stored API key found.")
                self.ai_status_label.setText("AI Engine: Key Not Configured")
        except Exception as e:
            logger.error(f"Failed to load secure key: {e}")
            self.ai_status_label.setText("AI Engine: Security Error")

    def _current_model_name(self):
        return self.gemini_model_selector.text().strip() or DEFAULT_MODEL

    @asyncSlot()
    async def _save_and_test_gemini_key(self):
        """Saves and tests Gemini API Key."""
        api_key = self.gemini_api_key_input.text().strip()
        model_name = self._current_model_name()

        if api_key != MASKED_KEY:
            if not api_key:
                show_error_message("Validation Error", "API Key cannot be blank.")
                return
            try:
                self.ai_provider.save_api_key_securely(api_key)
                self.ai_provider.set_api_key(api_key)
            except Exception as e:
                show_error_message("Storage Error", f"Could not save API key: {e}")
                return

        # Save model preference to config JSON
        config = load_config()
        config["gemini_model"] = model_name
        save_config(config)
        self.ai_provider.set_model(model_name)
        self.model_status_label.setText(f"Active Model: {model_name}")

        self.save_key_button.setEnabled(False)
        self.ai_status_label.setText("AI Engine: Testing Connection...")
        self.ai_state_changed.emit("thinking")

        try:
            ok = await asyncio.to_thread(self.ai_provider.test_connection, model_name)
            if ok:
                show_info_message("Success", "Successfully connected to Gemini API!")
                self.ai_status_label.setText("AI Engine: Online & Ready")
                self.gemini_api_key_input.setText(MASKED_KEY)
            else:
                show_error_message("Connection Failed", "Unable to connect with provided credentials/model.")
                self.ai_status_label.setText("AI Engine: Connection Failed")
        except Exception as e:
            show_error_message("Test Error", str(e))
            self.ai_status_label.setText("AI Engine: Test Error")
        finally:
            self.save_key_button.setEnabled(True)
            self.ai_state_changed.emit("idle")

    # ------------------------------------------------------------------ Chat Slot

    @asyncSlot()
    async def _send_command(self):
        """Handles sending a command to JARVIS AI."""
        if self._busy:
            return

        user_text = self.command_input.text().strip()
        if not user_text:
            return

        if not self.ai_provider.is_configured():
            show_error_message("Configuration Needed",
                               "Gemini API key is not configured. Please set it in Settings.")
            return

        model_name = self._current_model_name()
        self.command_input.clear()
        self._append_message("User", user_text)

        formatted_history = self._build_gemini_history()

        self._set_busy(True)
        self._idle_timer.stop()
        self.ai_state_changed.emit("thinking")
        self.ai_status_label.setText("AI Engine: Generating Response...")

        try:
            response_text = await asyncio.to_thread(
                self.ai_provider.send_message, formatted_history, model_name
            )
            self._handle_gemini_response(response_text)
        except Exception as e:
            logger.exception("Error processing AI request.")
            self._handle_gemini_error(str(e))
        finally:
            self._set_busy(False)

    def _build_gemini_history(self):
        """Converts conversation history to Gemini list format."""
        return [
            {"role": "user" if role == "User" else "model", "parts": [text]}
            for role, text in self.conversation_history
        ]

    def _set_busy(self, busy):
        self._busy = busy
        self.send_button.setEnabled(not busy)
        self.command_input.setEnabled(not busy)
        if not busy:
            self.command_input.setFocus()

    def _handle_gemini_response(self, response_text):
        self._append_message("JARVIS", response_text)
        self.ai_state_changed.emit("speaking")
        self.ai_status_label.setText("AI Engine: Online & Ready")
        self._idle_timer.start(2500)

    def _handle_gemini_error(self, error_msg):
        if self.conversation_history and self.conversation_history[-1][0] == "User":
            self.conversation_history.pop()

        self._append_message("JARVIS (System)", f"Error: {error_msg}", store=False)
        self.ai_state_changed.emit("error")
        self.ai_status_label.setText("AI Engine: Error")
        self._idle_timer.start(4000)

    def _append_message(self, sender, text, store=True):
        if store:
            self.conversation_history.append((sender, text))

        color_map = {
            "User": "#00C8FF",
            "JARVIS": "#7FFFD4",
            "JARVIS (System)": "#FF6B6B"
        }
        color = color_map.get(sender, "#E0E0E0")
        safe_text = html.escape(str(text)).replace("\n", "<br>")

        formatted_msg = (
            f'<div style="margin-bottom: 12px;">'
            f'<b style="color: {color}; font-size: 11pt;">{html.escape(sender)}:</b><br>'
            f'<span style="color: #F0F4F8; font-size: 10pt; line-height: 1.4;">{safe_text}</span>'
            f'</div>'
        )

        self.conversation_display.append(formatted_msg)
        bar = self.conversation_display.verticalScrollBar()
        bar.setValue(bar.maximum())
