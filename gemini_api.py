# JARVIS_AI/gemini_api.py
import logging
import sys
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import (
    GoogleAPIError, InvalidArgument, ResourceExhausted, ServiceUnavailable,
    InternalServerError, ClientError
)
import requests # For network-specific exceptions
from config import get_secret, set_secret # For secure API key management

logger = logging.getLogger(__name__)

class GeminiAIProvider:
    """
    Provides an interface for interacting with the Google Gemini AI API.
    Handles API key management, model selection, conversation history,
    and error handling.
    """
    DEFAULT_MODEL = "gemini-pro" # A good general-purpose model for text chat
    SAFETY_SETTINGS = [
        {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    ]

    def __init__(self):
        """
        Initializes the Gemini AI provider.
        Does NOT attempt to configure genai or initialize model here.
        Relies on set_api_key being called after key retrieval.
        """
        self._api_key = None
        self._model_name = self.DEFAULT_MODEL
        self._model = None
        logger.info("GeminiAIProvider initialized. Awaiting API key configuration.")

    def _initialize_model(self):
        """
        Initializes the GenerativeModel instance with the current API key and model name.
        This must be called AFTER genai.configure(api_key=...) has been run.
        """
        if not self._api_key:
            self._model = None
            logger.warning("Cannot initialize Gemini model: API key is not set.")
            return

        try:
            # genai.configure(api_key=self._api_key) # Already done by set_api_key
            self._model = genai.GenerativeModel(
                model_name=self._model_name,
                safety_settings=self.SAFETY_SETTINGS
            )
            logger.info(f"Gemini model '{self._model_name}' initialized successfully.")
        except ValueError as e:
            logger.error(f"Failed to initialize Gemini model '{self._model_name}': {e}")
            self._model = None
            raise ValueError(f"Invalid model name or configuration for '{self._model_name}'.") from e
        except Exception as e:
            logger.exception(f"An unexpected error occurred during Gemini model initialization for '{self._model_name}'.")
            self._model = None
            raise RuntimeError(f"Failed to initialize Gemini model: {e}") from e

    def save_api_key_securely(self, api_key: str):
        """
        Securely stores the Gemini API key using the config module.
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty.")
        set_secret("gemini_api_key", api_key.strip())
        logger.info("Gemini API key saved securely via config module.")

    def get_api_key_securely(self) -> str | None:
        """
        Retrieves the Gemini API key securely from the config module.
        """
        key = get_secret("gemini_api_key")
        if key:
            logger.debug("Gemini API key retrieved securely.")
        return key

    def set_api_key(self, api_key: str):
        """
        Configures the google.generativeai library with the provided API key
        for the current session and attempts to initialize the model.
        This does NOT save the key to persistent storage.
        """
        if not api_key or not api_key.strip():
            self._api_key = None
            self._model = None
            genai.configure(api_key=None) # Clear configuration
            logger.warning("Gemini API key cleared.")
            return

        self._api_key = api_key.strip()
        try:
            genai.configure(api_key=self._api_key)
            self._initialize_model()
            logger.info("Gemini API configured for current session.")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API with provided key: {e}")
            self._model = None
            raise ValueError(f"Invalid API key format or configuration issue: {e}") from e

    def set_model(self, model_name: str):
        """
        Sets the Gemini model to be used for generation.
        Re-initializes the model with the new name.
        """
        if not model_name or not model_name.strip():
            raise ValueError("Model name cannot be empty.")
        if self._model_name != model_name.strip():
            self._model_name = model_name.strip()
            # Re-initialize model with the new name if API key is already set
            if self._api_key:
                self._initialize_model()
            logger.info(f"Gemini model name updated to '{self._model_name}'.")

    def get_available_models(self) -> list[str]:
        """
        Fetches a list of available Gemini models that support generateContent.
        Requires an API key to be set.
        """
        if not self._api_key:
            logger.warning("Cannot get available models: API key is not set.")
            raise RuntimeError("Gemini API key is not set. Please configure it in settings.")
        try:
            models = genai.list_models()
            available_models = [
                m.name for m in models
                if 'generateContent' in m.supported_generation_methods
            ]
            logger.info(f"Found {len(available_models)} available Gemini models.")
            return available_models
        except ValueError as e:
            logger.error(f"Invalid API key when listing models: {e}")
            raise ValueError("Invalid Gemini API Key. Please check your key.") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error when listing models: {e}")
            raise ConnectionError("Network error. Please check your internet connection.") from e
        except GoogleAPIError as e:
            logger.error(f"Google API error when listing models: {e.message}")
            raise RuntimeError(f"Gemini API error: {e.message}") from e
        except Exception as e:
            logger.exception("An unexpected error occurred while listing Gemini models.")
            raise RuntimeError(f"An unexpected error occurred: {e}") from e

    def test_connection(self) -> tuple[bool, str]:
        """
        Tests the connection to the Gemini API using the current API key and model.
        Returns (True, "Success message") or (False, "Error message").
        """
        if not self._api_key:
            return False, "API key is not set. Please enter your Gemini API key in settings."
        if not self._model:
            return False, f"Model '{self._model_name}' could not be initialized. Check API key and model name."

        try:
            # Attempt to list models to verify API key and connectivity
            # This is a good lightweight test
            self.get_available_models()
            return True, f"Successfully connected to Gemini API with model '{self._model_name}'."
        except ValueError as e:
            return False, f"Connection failed: {e}"
        except ConnectionError as e:
            return False, f"Connection failed: {e}"
        except RuntimeError as e:
            return False, f"Connection failed: {e}"
        except Exception as e:
            logger.exception("An unexpected error occurred during Gemini connection test.")
            return False, f"An unexpected error occurred: {e}"

    def send_message(self, user_message: str, history: list) -> tuple[str | None, list]:
        """
        Sends a message to the Gemini model and retrieves its response.
        Manages conversation history.

        Args:
            user_message (str): The user's current message.
            history (list): A list of (role, text) tuples representing the conversation.
                            Roles are "User" and "JARVIS" as per jarvis_ui.py.

        Returns:
            tuple[str | None, list]: (AI response text, updated conversation history).
                                     AI response text is None if an error occurred.
        """
        if not self._api_key or not self._model:
            raise RuntimeError("Gemini API not configured. Please set your API key in settings.")
        if not user_message.strip():
            return None, history # No message to send

        # Convert history from (role, text) tuples to Gemini's expected format
        # Gemini roles are 'user' and 'model'
        formatted_history = []
        for role, text in history:
            gemini_role = 'user' if role == 'User' else 'model' # Map "User" to 'user', "JARVIS" to 'model'
            formatted_history.append({'role': gemini_role, 'parts': [{'text': text}]})

        try:
            # Start a chat session with the formatted history
            chat = self._model.start_chat(history=formatted_history)
            response = chat.send_message(user_message)

            ai_response_text = ""
            if response.candidates:
                # Access the first candidate's content parts
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        ai_response_text += part.text
            else:
                # Handle cases where no candidates are returned (e.g., safety block)
                if response.prompt_feedback and response.prompt_feedback.safety_ratings:
                    safety_feedback = ", ".join([
                        f"{s.category.name}: {s.probability.name}"
                        for s in response.prompt_feedback.safety_ratings
                    ])
                    ai_response_text = f"JARVIS: I cannot respond to that due to safety concerns. Feedback: {safety_feedback}"
                    logger.warning(f"Gemini blocked response due to safety: {safety_feedback}")
                else:
                    ai_response_text = "JARVIS: I'm sorry, I couldn't generate a response. The model returned no candidates."
                    logger.warning("Gemini returned no candidates and no specific safety feedback.")

            # Update history with the new user message and AI response
            updated_history = history + [('User', user_message), ('JARVIS', ai_response_text)]
            return ai_response_text, updated_history

        except InvalidArgument as e:
            logger.error(f"Gemini API Invalid Argument: {e}")
            raise ValueError(f"Gemini API Error: Invalid argument provided. This might be due to content safety or malformed input. Details: {e}") from e
        except ResourceExhausted as e:
            logger.error(f"Gemini API Quota Exceeded or Rate Limit: {e}")
            raise RuntimeError(f"Gemini API Error: You have exceeded your quota or rate limit. Please check your Google Cloud project settings or try again later. Details: {e}") from e
        except ServiceUnavailable as e:
            logger.error(f"Gemini API Service Unavailable: {e}")
            raise ConnectionError(f"Gemini API Error: Service is temporarily unavailable. Please try again shortly. Details: {e}") from e
        except InternalServerError as e:
            logger.error(f"Gemini API Internal Server Error: {e}")
            raise RuntimeError(f"Gemini API Error: An internal server error occurred. Please try again. Details: {e}") from e
        except ClientError as e:
            logger.error(f"Gemini API Client Error: {e}")
            raise RuntimeError(f"Gemini API Error: A client-side error occurred. Details: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during Gemini API call: {e}")
            raise ConnectionError(f"Network error. Please check your internet connection. Details: {e}") from e
        except GoogleAPIError as e:
            logger.error(f"General Google API error during Gemini call: {e}")
            raise RuntimeError(f"Gemini API Error: An unexpected API error occurred. Details: {e}") from e
        except Exception as e:
            logger.exception("An unexpected error occurred during Gemini message sending.")
            raise RuntimeError(f"An unexpected error occurred: {e}") from e
