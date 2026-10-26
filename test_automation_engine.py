import time
import pytest
from automation_engine import AutomationEngine, get_automation_log


def test_launch_application():
    res = AutomationEngine.launch_application("calculator")
    assert isinstance(res, dict)
    assert "success" in res
    assert "message" in res
    assert res["app_name"] == "calculator"


def test_schedule_app_launch():
    callback_called = []

    def on_done(res):
        callback_called.append(res)

    res = AutomationEngine.schedule_app_launch("calc", 0.1, callback=on_done)
    assert res["success"] is True
    assert res["delay_seconds"] == 0.1

    time.sleep(0.3)
    assert len(callback_called) == 1


def test_open_url_and_weather():
    res_url = AutomationEngine.open_url("https://example.com")
    assert res_url["success"] is True

    res_weather = AutomationEngine.open_weather("New York")
    assert res_weather["success"] is True


def test_send_email():
    res = AutomationEngine.send_email(
        to_email="test@example.com",
        subject="Test Subject",
        body="Test Body"
    )
    assert res["success"] is True
    assert res["to_email"] == "test@example.com"


def test_parse_and_execute():
    res1 = AutomationEngine.parse_and_execute("open calculator")
    assert res1 is not None
    assert res1["app_name"] == "calculator"

    res2 = AutomationEngine.parse_and_execute("open notepad in 5 seconds")
    assert res2 is not None
    assert res2["app_name"] == "notepad"
    assert res2["delay_seconds"] == 5.0

    res3 = AutomationEngine.parse_and_execute("watch the weather tomorrow")
    assert res3 is not None
    assert "Weather" in res3["message"] or "weather" in res3["message"]

    res4 = AutomationEngine.parse_and_execute("email user@domain.com Hello there")
    assert res4 is not None
    assert res4["to_email"] == "user@domain.com"
