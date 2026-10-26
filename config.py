# JARVIS_AI/config.py
import keyring
import logging
import json
import os

logger = logging.getLogger(__name__)

APP_NAME = "JARVIS_AI"
CONFIG_FILE = "jarvis_config.json" # For non-sensitive settings like model name

def _get_config_dir() -> str:
    """Returns the path to the application's configuration directory."""
    # Use APPDATA on Windows, or ~/.config on Linux/macOS
    if sys.platform == "win32":
        app_data_path = os.environ.get('APPDATA')
        if not app_data_path:
            app_data_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
    else:
        app_data_path = os.path.join(os.path.expanduser('~'), '.config')

    config_dir = os.path.join(app_data_path, APP_NAME)
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def load_config() -> dict:
    """Loads non-sensitive application settings from a JSON file."""
    config_path = os.path.join(_get_config_dir(), CONFIG_FILE)
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            logger.info(f"Settings loaded from {config_path}")
            return settings
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load settings from {config_path}: {e}")
            return {}
    logger.info(f"No settings file found at {config_path}. Returning empty config.")
    return {}

def save_config(settings: dict):
    """Saves non-sensitive application settings to a JSON file."""
    config_path = os.path.join(_get_config_dir(), CONFIG_FILE)
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        logger.info(f"Settings saved to {config_path}")
    except Exception as e:
        logger.error(f"Failed to save settings to {config_path}: {e}")

def get_secret(key_name: str) -> str | None:
    """
    Retrieves a secret (e.g., API key) from the OS-backed secure credential store.
    Uses keyring for cross-platform compatibility.
    """
    try:
        secret = keyring.get_password(APP_NAME, key_name)
        if secret:
            logger.debug(f"Secret '{key_name}' retrieved successfully.")
        else:
            logger.debug(f"Secret '{key_name}' not found in credential store.")
        return secret
    except keyring.errors.NoKeyringError:
        logger.error("No keyring backend found. Please install a suitable backend (e.g., 'keyrings.alt').")
        raise RuntimeError("No secure credential store backend found. Please install 'keyrings.alt' or configure your system's keyring.")
    except Exception as e:
        logger.error(f"Failed to retrieve secret '{key_name}': {e}")
        return None

def set_secret(key_name: str, value: str):
    """
    Stores a secret (e.g., API key) in the OS-backed secure credential store.
    """
    try:
        keyring.set_password(APP_NAME, key_name, value)
        logger.info(f"Secret '{key_name}' stored successfully.")
    except keyring.errors.NoKeyringError:
        logger.error("No keyring backend found. Please install a suitable backend (e.g., 'keyrings.alt').")
        raise RuntimeError("No secure credential store backend found. Please install 'keyrings.alt' or configure your system's keyring.")
    except Exception as e:
        logger.error(f"Failed to store secret '{key_name}': {e}")
        raise
