import asyncio
import sys
import pytest
from PySide6.QtWidgets import QApplication

import Jarvis_UI
from automation_engine import AutomationEngine, get_automation_log
from memory_manager import MemoryManager
from task_manager import TaskManager

Jarvis_UI.show_error_message = lambda title, msg: print(f"[MOCK DIALOG - ERROR] {title}: {msg}")
Jarvis_UI.show_info_message = lambda title, msg: print(f"[MOCK DIALOG - INFO] {title}: {msg}")


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_ui_tab_switching(qapp):
    window = Jarvis_UI.JarvisMainWindow()
    assert window.stacked_widget.currentIndex() == 0

    for idx in range(6):
        window.stacked_widget.setCurrentIndex(idx)
        assert window.stacked_widget.currentIndex() == idx


def test_chat_command_automation_integration(qapp):
    async def run_tests():
        window = Jarvis_UI.JarvisMainWindow()
        send_cmd = window._send_command.__wrapped__

        window.command_input.setText("open calculator")
        await send_cmd(window)
        assert any("open calculator" in msg[1] for msg in window.conversation_history if msg[0] == "User")
        assert any("Action Executed" in msg[1] or "Notice" in msg[1] for msg in window.conversation_history if msg[0] == "JARVIS")

        window.command_input.setText("open notepad in 1 seconds")
        await send_cmd(window)
        assert any("notepad" in msg[1] for msg in window.conversation_history if msg[0] == "JARVIS")

        window.command_input.setText("watch the weather tomorrow")
        await send_cmd(window)
        assert any("weather" in msg[1].lower() for msg in window.conversation_history if msg[0] == "JARVIS")

        window.command_input.setText("email alex@test.com subject Hi body Testing email automation")
        await send_cmd(window)
        assert any("alex@test.com" in msg[1] for msg in window.conversation_history if msg[0] == "JARVIS")

        window.command_input.setText("remember that my favorite programming language is Python")
        await send_cmd(window)
        memories = MemoryManager.get_all_memories()
        assert any("favorite programming language is Python" in m["text"] for m in memories)

        window.command_input.setText("add task Prepare presentation for team")
        await send_cmd(window)
        tasks = TaskManager.get_all_tasks()
        assert any("Prepare presentation for team" in t["title"] for t in tasks)

    asyncio.run(run_tests())
