# JARVIS_AI/config.py
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile

import keyring
from keyring.errors import NoKeyringError

logger = logging.getLogger(__name__)

APP_NAME = "JARVIS_AI"
CONFIG_FILE = "jarvis_config.json"  # For non-sensitive settings like model name

_NO_BACKEND_MESSAGE = (
    "No secure credential store backend found. On Linux, install and unlock a "
    "Secret Service provider (GNOME Keyring or KWallet). 'keyrings.alt' also "
    "works but stores secrets unencrypted, so use it only as a last resort."
)


def _get_config_dir() -> str:
    """Returns the path to the application's configuration directory (created if missing)."""
    if sys.platform == "win32":
        base_path = os.environ.get("APPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Roaming"
        )
    else:
        base_path = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )

    config_dir = os.path.join(base_path, APP_NAME)
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def load_config() -> dict:
    """Loads non-sensitive application settings from a JSON file."""
    config_path = os.path.join(_get_config_dir(), CONFIG_FILE)
    if not os.path.exists(config_path):
        logger.info(f"No settings file found at {config_path}. Returning empty config.")
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {config_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load settings from {config_path}: {e}")
        return {}

    if not isinstance(settings, dict):
        logger.error(f"Settings file {config_path} does not contain a JSON object. Ignoring it.")
        return {}

    logger.info(f"Settings loaded from {config_path}")
    return settings


def save_config(settings: dict) -> bool:
    """
    Saves non-sensitive application settings to a JSON file.
    Returns True on success, False if the file could not be written.
    """
    if not isinstance(settings, dict):
        raise TypeError(
            f"save_config() expects a dict, got {type(settings).__name__}"
        )

    config_path = os.path.join(_get_config_dir(), CONFIG_FILE)
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(config_path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        os.replace(tmp_path, config_path)
        tmp_path = None
        logger.info(f"Settings saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save settings to {config_path}: {e}")
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def get_secret(key_name: str) -> str | None:
    """
    Retrieves a secret (e.g., API key) from the OS-backed secure credential store.
    Falls back to local application config if no OS keyring backend is installed.
    """
    try:
        secret = keyring.get_password(APP_NAME, key_name)
        if secret:
            logger.debug(f"Secret '{key_name}' retrieved successfully from OS keyring.")
            return secret
    except NoKeyringError:
        logger.warning("No keyring backend found; attempting fallback config store.")
    except Exception as e:
        logger.error(f"Failed to retrieve secret '{key_name}' from keyring: {e}")

    app_config = load_config()
    return app_config.get(f"_secret_{key_name}")


def set_secret(key_name: str, value: str) -> None:
    """Stores a secret (e.g., API key) in the OS-backed credential store or local fallback store."""
    stored_in_keyring = False
    try:
        keyring.set_password(APP_NAME, key_name, value)
        stored_in_keyring = True
        logger.info(f"Secret '{key_name}' stored successfully in OS keyring.")
    except NoKeyringError:
        logger.warning("No keyring backend found; storing secret in local config store.")
    except Exception as e:
        logger.error(f"Failed to store secret '{key_name}' in keyring: {e}")

    if not stored_in_keyring:
        app_config = load_config()
        app_config[f"_secret_{key_name}"] = value
        save_config(app_config)
        logger.info(f"Secret '{key_name}' saved to fallback config store.")
