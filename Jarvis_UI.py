import asyncio
import html
import logging

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from ai_core_visualization import AICoreVisualization
from automation_engine import AutomationEngine, get_automation_log
from config import load_config, save_config
from gemini_api import GeminiAIProvider
from gui_components import LiquidGlassBackground, LiquidGlassCard
from memory_manager import MemoryManager
from task_manager import TaskManager
from utils import show_error_message, show_info_message

logger = logging.getLogger(__name__)

MASKED_KEY = "********"
DEFAULT_MODEL = "gemini-1.5-flash"


# ==============================================================================
# FEATURE VIEWS
# ==============================================================================

class EmailView(LiquidGlassCard):
    """Production-ready Email Automation View."""

    def __init__(self, parent=None):
        super().__init__(parent, corner_radius=24)
        self._setup_ui()
        self.load_settings_and_history()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(QLabel("<h2 style='color: #00C8FF; margin:0;'>📧 Email Integration & Automation</h2>"))

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # 1. SMTP Config Card
        smtp_card = LiquidGlassCard(scroll_content, corner_radius=16)
        smtp_layout = QVBoxLayout(smtp_card)
        smtp_layout.addWidget(QLabel("<h3 style='color: #7FFFD4; margin:0;'>SMTP Configuration</h3>"))

        smtp_grid = QHBoxLayout()
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("SMTP Host (e.g. smtp.gmail.com)")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Port (587)")
        self.port_input.setFixedWidth(90)
        smtp_grid.addWidget(self.server_input)
        smtp_grid.addWidget(self.port_input)
        smtp_layout.addLayout(smtp_grid)

        smtp_cred_grid = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("SMTP Username / Email")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("SMTP Password / App Key")
        smtp_cred_grid.addWidget(self.user_input)
        smtp_cred_grid.addWidget(self.pass_input)
        smtp_layout.addLayout(smtp_cred_grid)

        save_smtp_btn = QPushButton("Save SMTP Credentials")
        save_smtp_btn.clicked.connect(self._save_smtp_config)
        smtp_layout.addWidget(save_smtp_btn)
        scroll_layout.addWidget(smtp_card)

        # 2. Compose Email Card
        compose_card = LiquidGlassCard(scroll_content, corner_radius=16)
        compose_layout = QVBoxLayout(compose_card)
        compose_layout.addWidget(QLabel("<h3 style='color: #00C8FF; margin:0;'>Compose & Send Email</h3>"))

        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("Recipient Email (e.g. user@example.com)")
        compose_layout.addWidget(self.to_input)

        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Email Subject")
        compose_layout.addWidget(self.subject_input)

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Type your email body message here...")
        self.body_input.setFixedHeight(120)
        compose_layout.addWidget(self.body_input)

        send_btn = QPushButton("🚀 Send Email Now")
        send_btn.setFixedHeight(38)
        send_btn.clicked.connect(self._send_email)
        compose_layout.addWidget(send_btn)
        scroll_layout.addWidget(compose_card)

        # 3. Email History
        history_card = LiquidGlassCard(scroll_content, corner_radius=16)
        history_layout = QVBoxLayout(history_card)
        history_layout.addWidget(QLabel("<h3 style='color: #00C8FF; margin:0;'>Dispatched Email Log</h3>"))

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setFixedHeight(150)
        history_layout.addWidget(self.history_display)
        scroll_layout.addWidget(history_card)

    def load_settings_and_history(self):
        cfg = load_config()
        smtp = cfg.get("smtp", {})
        self.server_input.setText(smtp.get("server", ""))
        self.port_input.setText(str(smtp.get("port", 587)))
        self.user_input.setText(smtp.get("username", ""))
        self.pass_input.setText(smtp.get("password", ""))

        self.refresh_history()

    def refresh_history(self):
        cfg = load_config()
        history = cfg.get("email_history", [])
        if not history:
            self.history_display.setText("No dispatched emails recorded yet.")
            return

        lines = []
        for item in reversed(history):
            lines.append(f"[{item.get('timestamp')}] To: {item.get('to_email')} | Subject: {item.get('subject')}\n  {item.get('body')}\n")
        self.history_display.setText("\n".join(lines))

    def _save_smtp_config(self):
        cfg = load_config()
        try:
            port = int(self.port_input.text().strip() or "587")
        except ValueError:
            port = 587

        cfg["smtp"] = {
            "server": self.server_input.text().strip(),
            "port": port,
            "username": self.user_input.text().strip(),
            "password": self.pass_input.text().strip()
        }
        save_config(cfg)
        show_info_message("Saved", "SMTP Server configuration saved successfully.")

    def _send_email(self):
        to_addr = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()

        if not to_addr or not body:
            show_error_message("Missing Input", "Please provide recipient address and body content.")
            return

        res = AutomationEngine.send_email(to_addr, subject or "Message from JARVIS AI", body)
        if res["success"]:
            show_info_message("Success", res["message"])
            self.to_input.clear()
            self.subject_input.clear()
            self.body_input.clear()
            self.refresh_history()
        else:
            show_error_message("Error", res["message"])


class AutomationView(LiquidGlassCard):
    """Production-ready Windows / OS Desktop Automation View."""

    def __init__(self, parent=None):
        super().__init__(parent, corner_radius=24)
        self._setup_ui()
        self._start_timer()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(QLabel("<h2 style='color: #00C8FF; margin:0;'>⚡ Desktop Automation & Computer Control</h2>"))

        # Quick Launcher Card
        quick_card = LiquidGlassCard(self, corner_radius=16)
        quick_layout = QVBoxLayout(quick_card)
        quick_layout.addWidget(QLabel("<h3 style='color: #7FFFD4; margin:0;'>Quick App Launcher</h3>"))

        btn_grid = QHBoxLayout()
        apps = [
            ("📝 Notepad", "notepad"),
            ("🧮 Calculator", "calculator"),
            ("🌐 Web Browser", "browser"),
            ("💻 Terminal", "terminal"),
            ("📁 Explorer", "files"),
            ("🌤️ Weather", "weather"),
        ]

        for label, app_cmd in apps:
            btn = QPushButton(label)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda _, a=app_cmd: self._trigger_app(a))
            btn_grid.addWidget(btn)

        quick_layout.addLayout(btn_grid)
        layout.addWidget(quick_card)

        # Custom Launcher Card
        custom_card = LiquidGlassCard(self, corner_radius=16)
        custom_layout = QVBoxLayout(custom_card)
        custom_layout.addWidget(QLabel("<h3 style='color: #00C8FF; margin:0;'>Custom Launcher & Scheduled Timer</h3>"))

        input_row = QHBoxLayout()
        self.app_input = QLineEdit()
        self.app_input.setPlaceholderText("App or command name (e.g. code, chrome, calc, spotify...)")

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 3600)
        self.delay_spin.setSuffix(" sec delay")
        self.delay_spin.setFixedWidth(120)

        run_btn = QPushButton("▶ Launch App")
        run_btn.setFixedHeight(36)
        run_btn.clicked.connect(self._run_custom_app)

        input_row.addWidget(self.app_input)
        input_row.addWidget(self.delay_spin)
        input_row.addWidget(run_btn)
        custom_layout.addLayout(input_row)

        layout.addWidget(custom_card)

        # Activity Execution Log
        log_card = LiquidGlassCard(self, corner_radius=16)
        log_layout = QVBoxLayout(log_card)
        log_layout.addWidget(QLabel("<h3 style='color: #00C8FF; margin:0;'>Automation Activity Log</h3>"))

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        layout.addWidget(log_card, stretch=1)

    def _trigger_app(self, app_cmd: str):
        if app_cmd == "weather":
            res = AutomationEngine.open_weather()
        else:
            res = AutomationEngine.launch_application(app_cmd)
        self.refresh_log()

    def _run_custom_app(self):
        app_name = self.app_input.text().strip()
        if not app_name:
            show_error_message("Missing App", "Please enter an application name.")
            return

        delay = self.delay_spin.value()
        if delay > 0:
            AutomationEngine.schedule_app_launch(app_name, float(delay))
            show_info_message("Scheduled", f"Scheduled '{app_name}' to open in {delay} seconds.")
        else:
            res = AutomationEngine.launch_application(app_name)
            show_info_message("Launched", res["message"])

        self.app_input.clear()
        self.delay_spin.setValue(0)
        self.refresh_log()

    def _start_timer(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_log)
        self._timer.start(2000)

    def refresh_log(self):
        logs = get_automation_log()
        if not logs:
            self.log_display.setText("No automation actions recorded yet.")
            return

        lines = []
        for entry in reversed(logs):
            lines.append(f"[{entry['timestamp']}] [{entry['status']}] {entry['action']}: {entry['details']}")
        self.log_display.setText("\n".join(lines))


class TasksView(LiquidGlassCard):
    """Production-ready Task & Reminder Management View."""

    def __init__(self, parent=None):
        super().__init__(parent, corner_radius=24)
        self._setup_ui()
        self.refresh_tasks()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(QLabel("<h2 style='color: #00C8FF; margin:0;'>📋 Task & Goal Management</h2>"))

        # Add Task Form Card
        add_card = LiquidGlassCard(self, corner_radius=16)
        add_layout = QVBoxLayout(add_card)
        add_layout.addWidget(QLabel("<h3 style='color: #7FFFD4; margin:0;'>Create New Task</h3>"))

        form_row = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task Title...")

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description (Optional)")

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Medium", "High", "Low"])
        self.priority_combo.setFixedWidth(100)

        add_btn = QPushButton("➕ Add Task")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_task)

        form_row.addWidget(self.title_input, stretch=2)
        form_row.addWidget(self.desc_input, stretch=2)
        form_row.addWidget(self.priority_combo)
        form_row.addWidget(add_btn)
        add_layout.addLayout(form_row)
        layout.addWidget(add_card)

        # Filter & Action bar
        filter_row = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["all", "pending", "completed"])
        self.filter_combo.currentTextChanged.connect(lambda _: self.refresh_tasks())
        filter_row.addWidget(QLabel("Filter:"))
        filter_row.addWidget(self.filter_combo)

        filter_row.addStretch()

        clear_completed_btn = QPushButton("🧹 Clear Completed")
        clear_completed_btn.clicked.connect(self._clear_completed)
        filter_row.addWidget(clear_completed_btn)
        layout.addLayout(filter_row)

        # Task Table Display
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Priority", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(15, 23, 42, 180);
                gridline-color: rgba(0, 200, 255, 40);
                border-radius: 10px;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: rgba(0, 200, 255, 60);
                color: #FFFFFF;
                padding: 6px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table, stretch=1)

    def _add_task(self):
        title = self.title_input.text().strip()
        desc = self.desc_input.text().strip()
        prio = self.priority_combo.currentText()

        if not title:
            show_error_message("Missing Title", "Please enter a task title.")
            return

        TaskManager.add_task(title, description=desc, priority=prio)
        self.title_input.clear()
        self.desc_input.clear()
        self.refresh_tasks()

    def _clear_completed(self):
        TaskManager.clear_completed_tasks()
        self.refresh_tasks()

    def refresh_tasks(self):
        filter_status = self.filter_combo.currentText()
        tasks = TaskManager.get_all_tasks(filter_status=filter_status)

        self.table.setRowCount(0)
        for row, t in enumerate(tasks):
            self.table.insertRow(row)

            item_id = QTableWidgetItem(t.get("id", ""))
            item_title = QTableWidgetItem(f"{t.get('title', '')}\n({t.get('description', '')})" if t.get('description') else t.get('title', ''))
            item_prio = QTableWidgetItem(t.get("priority", "Medium"))
            item_status = QTableWidgetItem(t.get("status", "pending"))

            self.table.setItem(row, 0, item_id)
            self.table.setItem(row, 1, item_title)
            self.table.setItem(row, 2, item_prio)
            self.table.setItem(row, 3, item_status)

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)

            if t.get("status") == "pending":
                done_btn = QPushButton("✓ Done")
                done_btn.setFixedHeight(26)
                done_btn.clicked.connect(lambda _, tid=t.get("id"): self._complete_task(tid))
                action_layout.addWidget(done_btn)

            del_btn = QPushButton("🗑️ Delete")
            del_btn.setFixedHeight(26)
            del_btn.clicked.connect(lambda _, tid=t.get("id"): self._delete_task(tid))
            action_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 4, action_widget)

    def _complete_task(self, task_id):
        TaskManager.mark_task_completed(task_id)
        self.refresh_tasks()

    def _delete_task(self, task_id):
        TaskManager.delete_task(task_id)
        self.refresh_tasks()


class MemoryView(LiquidGlassCard):
    """Production-ready Memory & Context View."""

    def __init__(self, parent=None):
        super().__init__(parent, corner_radius=24)
        self._setup_ui()
        self.refresh_memories()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(QLabel("<h2 style='color: #00C8FF; margin:0;'>🧠 Memory & Personalization Bank</h2>"))

        # Add Memory Form Card
        add_card = LiquidGlassCard(self, corner_radius=16)
        add_layout = QVBoxLayout(add_card)
        add_layout.addWidget(QLabel("<h3 style='color: #7FFFD4; margin:0;'>Store New Fact / Instruction</h3>"))

        form_row = QHBoxLayout()
        self.memory_input = QLineEdit()
        self.memory_input.setPlaceholderText("e.g. My preferred email signature is 'Best regards, Alex'...")

        self.category_combo = QComboBox()
        self.category_combo.addItems(["Preference", "Fact", "Instruction", "General"])
        self.category_combo.setFixedWidth(120)

        add_btn = QPushButton("💾 Save Memory")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_memory)

        form_row.addWidget(self.memory_input, stretch=1)
        form_row.addWidget(self.category_combo)
        form_row.addWidget(add_btn)
        add_layout.addLayout(form_row)
        layout.addWidget(add_card)

        # Search & Action Row
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter stored memories...")
        self.search_input.textChanged.connect(lambda _: self.refresh_memories())
        search_row.addWidget(self.search_input)

        clear_all_btn = QPushButton("🗑️ Clear All Memories")
        clear_all_btn.clicked.connect(self._clear_all)
        search_row.addWidget(clear_all_btn)
        layout.addLayout(search_row)

        # Memory Display List Card
        list_card = LiquidGlassCard(self, corner_radius=16)
        list_layout = QVBoxLayout(list_card)
        list_layout.addWidget(QLabel("<h3 style='color: #00C8FF; margin:0;'>Active Memory Bank Context</h3>"))

        self.memory_display = QTextEdit()
        self.memory_display.setReadOnly(True)
        list_layout.addWidget(self.memory_display)
        layout.addWidget(list_card, stretch=1)

    def _add_memory(self):
        text = self.memory_input.text().strip()
        cat = self.category_combo.currentText()

        if not text:
            show_error_message("Missing Memory", "Please enter memory text to save.")
            return

        MemoryManager.add_memory(text, category=cat)
        self.memory_input.clear()
        self.refresh_memories()

    def _clear_all(self):
        MemoryManager.clear_all_memories()
        self.refresh_memories()

    def refresh_memories(self):
        q = self.search_input.text().strip()
        memories = MemoryManager.search_memories(q)

        if not memories:
            self.memory_display.setText("No stored memories found.")
            return

        lines = []
        for m in memories:
            lines.append(f"[{m.get('id')}] [{m.get('category').upper()}] ({m.get('timestamp')})\n  {m.get('text')}\n")
        self.memory_display.setText("\n".join(lines))


# ==============================================================================
# MAIN WINDOW
# ==============================================================================

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
        self._busy = False
        self._sidebar_buttons = []

        # Timer to reset core visualization state back to idle
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(lambda: self.ai_state_changed.emit("idle"))

        self._setup_ui()
        self._load_settings()

        self.ai_state_changed.emit("idle")
        logger.info("JARVIS AI application initialized successfully.")

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

        # Production Views for Email, Automation, Tasks, Memory
        self.email_view = EmailView(self.content_area)
        self.stacked_widget.addWidget(self.email_view)  # 1

        self.automation_view = AutomationView(self.content_area)
        self.stacked_widget.addWidget(self.automation_view)  # 2

        self.tasks_view = TasksView(self.content_area)
        self.stacked_widget.addWidget(self.tasks_view)  # 3

        self.memory_view = MemoryView(self.content_area)
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
            QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QSpinBox {
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
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: rgba(15, 23, 42, 180);
                border: 1px solid rgba(0, 200, 255, 60);
                border-radius: 10px;
                padding: 8px 12px;
                selection-background-color: #00C8FF;
                selection-color: #000000;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
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
        """Updates active sidebar button styling and refreshes view data."""
        self._update_sidebar_styles(index)
        if index == 1:
            self.email_view.refresh_history()
        elif index == 2:
            self.automation_view.refresh_log()
        elif index == 3:
            self.tasks_view.refresh_tasks()
        elif index == 4:
            self.memory_view.refresh_memories()

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
        self.conversation_display.setPlaceholderText("JARVIS is ready. Ask me anything or control your computer!")
        chat_layout.addWidget(self.conversation_display, stretch=1)

        # Command input row
        input_panel = QWidget(self.chat_view)
        input_layout = QHBoxLayout(input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)

        self.command_input = QLineEdit(self.chat_view)
        self.command_input.setPlaceholderText("Ask JARVIS, open apps, send emails, or schedule tasks...")
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

        save_config({"gemini_model": model_name})
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
        """Handles sending a command to JARVIS AI with local desktop automation & context support."""
        if self._busy:
            return

        user_text = self.command_input.text().strip()
        if not user_text:
            return

        self.command_input.clear()
        self._append_message("User", user_text)

        # 1. Attempt natural language OS automation execution directly
        action_res = AutomationEngine.parse_and_execute(user_text)

        # 2. Check for explicit memory commands: "remember that..."
        if user_text.lower().startswith("remember that "):
            fact = user_text[14:].strip()
            if fact:
                MemoryManager.add_memory(fact, category="fact")
                self._append_message("JARVIS", f"I have committed that to long-term memory: '{fact}'")
                return

        # 3. Check for explicit task commands: "add task ..."
        if user_text.lower().startswith("add task "):
            task_title = user_text[9:].strip()
            if task_title:
                t = TaskManager.add_task(task_title)
                self._append_message("JARVIS", f"I have added the task to your list: '{t['title']}'")
                return

        # If direct OS action handled it, inform user and finish turn
        if action_res:
            if action_res.get("success"):
                reply = f"⚡ Action Executed: {action_res.get('message')}"
            else:
                reply = f"⚠️ Automation Notice: {action_res.get('message')}"
            self._handle_gemini_response(reply)
            return

        if not self.ai_provider.is_configured():
            show_error_message("Configuration Needed",
                               "Gemini API key is not configured. Please set it in Settings.")
            return

        model_name = self._current_model_name()

        # Inject long term memory into prompt history
        memory_ctx = MemoryManager.get_formatted_memory_context()
        formatted_history = self._build_gemini_history(extra_context=memory_ctx)

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

    def _build_gemini_history(self, extra_context: str = ""):
        """Converts conversation history to Gemini list format, appending user memory context if present."""
        history = [
            {"role": "user" if role == "User" else "model", "parts": [text]}
            for role, text in self.conversation_history
        ]

        if extra_context and history:
            latest_turn = history[-1]
            if latest_turn["role"] == "user":
                latest_turn["parts"][0] = f"{extra_context}\n\nUser Question:\n{latest_turn['parts'][0]}"

        return history

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
