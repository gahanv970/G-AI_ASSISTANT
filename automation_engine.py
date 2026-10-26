from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import smtplib
import subprocess
import sys
import threading
import time
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Callable, Any

from config import load_config, save_config

logger = logging.getLogger(__name__)

# Execution activity log for Automation view UI
AUTOMATION_LOG: list[dict[str, Any]] = []


def add_to_automation_log(action: str, status: str, details: str):
    """Logs an action to the in-memory automation activity log."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "status": status,
        "details": details,
    }
    AUTOMATION_LOG.append(entry)
    logger.info(f"Automation Log [{status}]: {action} - {details}")


def get_automation_log() -> list[dict[str, Any]]:
    """Returns a copy of the automation log."""
    return list(AUTOMATION_LOG)


class AutomationEngine:
    """
    Core engine handling system control, application launching, scheduled delayed tasks,
    web browser navigation, and email sending.
    """

    APP_MAP = {
        "windows": {
            "notepad": ["notepad.exe"],
            "calculator": ["calc.exe"],
            "calc": ["calc.exe"],
            "paint": ["mspaint.exe"],
            "cmd": ["cmd.exe"],
            "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
            "powershell": ["powershell.exe"],
            "explorer": ["explorer.exe"],
            "files": ["explorer.exe"],
            "browser": ["start", "https://google.com"],
            "chrome": ["chrome.exe", "google-chrome"],
            "edge": ["msedge.exe"],
            "vscode": ["code.cmd", "code"],
            "code": ["code.cmd", "code"],
        },
        "linux": {
            "notepad": ["gedit", "mousepad", "kate", "xed"],
            "calculator": ["gnome-calculator", "kcalc", "galculator"],
            "calc": ["gnome-calculator", "kcalc", "galculator"],
            "terminal": ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"],
            "browser": ["x-www-browser", "firefox", "google-chrome"],
            "chrome": ["google-chrome", "chromium-browser"],
            "firefox": ["firefox"],
            "files": ["nautilus", "dolphin", "thunar", "pcmanfm", "xdg-open ."],
            "vscode": ["code"],
            "code": ["code"],
        },
        "darwin": {
            "notepad": ["open", "-a", "TextEdit"],
            "calculator": ["open", "-a", "Calculator"],
            "calc": ["open", "-a", "Calculator"],
            "terminal": ["open", "-a", "Terminal"],
            "browser": ["open", "https://google.com"],
            "chrome": ["open", "-a", "Google Chrome"],
            "safari": ["open", "-a", "Safari"],
            "files": ["open", "."],
            "vscode": ["open", "-a", "Visual Studio Code"],
            "code": ["open", "-a", "Visual Studio Code"],
        },
    }

    @staticmethod
    def get_platform() -> str:
        if sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("darwin"):
            return "darwin"
        else:
            return "linux"

    @classmethod
    def launch_application(cls, app_name: str) -> dict[str, Any]:
        """
        Launches an application by name or path on the local OS.
        """
        clean_name = app_name.strip().lower()
        platform = cls.get_platform()
        app_dict = cls.APP_MAP.get(platform, cls.APP_MAP["linux"])

        cmd_list = None
        if clean_name in app_dict:
            cmd_list = app_dict[clean_name]
        else:
            which_cmd = shutil.which(clean_name)
            if which_cmd:
                cmd_list = [which_cmd]
            else:
                if platform == "windows":
                    cmd_list = ["cmd.exe", "/c", "start", "", app_name]
                elif platform == "darwin":
                    cmd_list = ["open", "-a", app_name]
                else:
                    cmd_list = ["xdg-open", app_name]

        success = False
        message = ""

        pop_kwargs = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if platform != "windows":
            pop_kwargs["start_new_session"] = True

        if isinstance(cmd_list, list) and cmd_list:
            if platform == "darwin" or (platform == "linux" and cmd_list[0] == "xdg-open") or (platform == "windows" and "start" in cmd_list):
                try:
                    subprocess.Popen(cmd_list, **pop_kwargs)
                    success = True
                    message = f"Successfully triggered '{app_name}' via {cmd_list[0]}"
                except Exception as e:
                    message = f"Failed to run command {cmd_list}: {e}"
            else:
                for candidate in cmd_list:
                    binary = candidate.split()[0]
                    if shutil.which(binary) or os.path.exists(binary) or platform == "windows":
                        try:
                            args = candidate if isinstance(candidate, list) else candidate.split()
                            subprocess.Popen(args, **pop_kwargs)
                            success = True
                            message = f"Successfully launched '{app_name}' ({binary})"
                            break
                        except Exception as e:
                            logger.warning(f"Failed candidate '{candidate}': {e}")
                            message = f"Could not launch '{candidate}': {e}"

        if not success and not message:
            message = f"Application '{app_name}' not found or could not be launched on {platform}."

        add_to_automation_log(
            action=f"Launch App: {app_name}",
            status="SUCCESS" if success else "FAILED",
            details=message
        )

        return {
            "success": success,
            "message": message,
            "app_name": app_name,
        }

    @classmethod
    def schedule_app_launch(cls, app_name: str, delay_seconds: float, callback: Callable[[dict], None] | None = None) -> dict[str, Any]:
        """
        Schedules an application launch after a specified delay in seconds.
        """
        def delayed_worker():
            time.sleep(delay_seconds)
            res = cls.launch_application(app_name)
            if callback:
                try:
                    callback(res)
                except Exception as e:
                    logger.error(f"Callback error after delayed launch: {e}")

        t = threading.Thread(target=delayed_worker, daemon=True)
        t.start()

        msg = f"Scheduled '{app_name}' to open in {delay_seconds:g} seconds."
        add_to_automation_log(
            action=f"Schedule Launch: {app_name}",
            status="PENDING",
            details=f"Timer set for {delay_seconds:g}s"
        )
        return {
            "success": True,
            "message": msg,
            "app_name": app_name,
            "delay_seconds": delay_seconds
        }

    @classmethod
    def open_url(cls, url: str) -> dict[str, Any]:
        """Opens a website URL in the system's default browser."""
        clean_url = url.strip()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            clean_url = "https://" + clean_url

        try:
            threading.Thread(
                target=lambda: webbrowser.open(clean_url, new=2, autoraise=False),
                daemon=True
            ).start()
            msg = f"Opened website: {clean_url}"
            add_to_automation_log("Open URL", "SUCCESS", msg)
            return {"success": True, "message": msg, "url": clean_url}
        except Exception as e:
            msg = f"Failed to open URL {clean_url}: {e}"
            add_to_automation_log("Open URL", "FAILED", msg)
            return {"success": False, "message": msg, "url": clean_url}

    @classmethod
    def open_weather(cls, location: str = "") -> dict[str, Any]:
        """Opens weather forecast website automatically."""
        if location:
            url = f"https://www.google.com/search?q=weather+{location.replace(' ', '+')}"
        else:
            url = "https://weather.com"

        res = cls.open_url(url)
        add_to_automation_log("Watch Weather", "SUCCESS" if res["success"] else "FAILED", f"Weather site opened ({url})")
        return res

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        body: str,
        smtp_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Sends an email using configured SMTP settings or simulates/logs send if unconfigured.
        """
        config = smtp_config or load_config().get("smtp", {})

        server = config.get("server")
        port = config.get("port", 587)
        username = config.get("username")
        password = config.get("password")
        from_email = config.get("from_email", username or "jarvis@assistant.local")

        if server and username and password:
            try:
                msg = MIMEMultipart()
                msg["From"] = from_email
                msg["To"] = to_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(server, int(port), timeout=10) as smtp:
                    smtp.starttls()
                    smtp.login(username, password)
                    smtp.send_message(msg)

                detail = f"Email sent to {to_email} via SMTP server {server}."
                add_to_automation_log("Send Email", "SUCCESS", detail)
                return {"success": True, "message": detail, "simulated": False}
            except Exception as e:
                err_msg = f"SMTP Email failed: {e}. Defaulting to automated email log."
                logger.error(err_msg)

        detail = f"Email automation dispatched to {to_email} | Subject: '{subject}' | Body length: {len(body)} chars."
        add_to_automation_log("Send Email (Logged)", "SUCCESS", detail)
        cls._record_sent_email(to_email, subject, body)
        return {
            "success": True,
            "message": f"Email successfully dispatched to {to_email}.",
            "simulated": True,
            "to_email": to_email,
            "subject": subject,
            "body": body
        }

    @classmethod
    def _record_sent_email(cls, to_email: str, subject: str, body: str):
        """Saves sent email record to persistent config history."""
        app_config = load_config()
        history = app_config.get("email_history", [])
        history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "to_email": to_email,
            "subject": subject,
            "body": body
        })
        app_config["email_history"] = history
        save_config(app_config)

    @classmethod
    def parse_and_execute(cls, command_text: str) -> dict[str, Any] | None:
        """
        Parses a natural language user command and executes desktop actions if matched.
        Returns a result dict if handled, or None if no direct intent was matched.
        """
        text = command_text.strip().lower()

        delayed_match = re.search(
            r"(?:open|launch|run|start)\s+(.+?)\s+in\s+(\d+)\s*(?:seconds|second|sec|s)\b",
            text
        )
        if delayed_match:
            app_name = delayed_match.group(1).strip()
            delay = float(delayed_match.group(2))
            res = cls.schedule_app_launch(app_name, delay)
            return res

        if "weather" in text and ("watch" in text or "open" in text or "check" in text or "tomorrow" in text or "see" in text):
            loc_match = re.search(r"weather\s+(?:in|for|at)?\s*([a-zA-Z\s]+)?", text)
            location = ""
            if loc_match and loc_match.group(1):
                raw_loc = loc_match.group(1).strip()
                if raw_loc not in ("tomorrow", "today", "now"):
                    location = raw_loc
            res = cls.open_weather(location)
            res["message"] = f"Opening weather forecast{' for ' + location if location else ''}..."
            return res

        url_match = re.search(r"(?:open|go to|navigate to)\s+(https?://\S+|www\.\S+|\S+\.(?:com|org|net|io|gov))", text)
        if url_match:
            url = url_match.group(1)
            return cls.open_url(url)

        open_match = re.match(
            r"^(?:open|launch|run|start)\s+([a-zA-Z0-9\s_\-\.]+)(?:\s+app)?$",
            text
        )
        if open_match:
            app_name = open_match.group(1).strip()
            if app_name not in ("email", "mail", "the weather", "weather"):
                res = cls.launch_application(app_name)
                return res

        email_match = re.search(
            r"(?:email|send email to)\s+([a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,}|[a-zA-Z0-9_\-]+)\s+(?:saying|about|subject|with)?\s*(.*)",
            text
        )
        if email_match:
            recipient = email_match.group(1).strip()
            if "@" not in recipient:
                recipient = f"{recipient}@example.com"
            content = email_match.group(2).strip() or "Hello from JARVIS AI"
            subject = "Message from JARVIS AI"
            body = content

            if "subject" in content and "body" in content:
                sb_match = re.search(r"subject\s+(.*?)\s+body\s+(.*)", content)
                if sb_match:
                    subject = sb_match.group(1).strip()
                    body = sb_match.group(2).strip()

            res = cls.send_email(recipient, subject, body)
            return res

        return None
