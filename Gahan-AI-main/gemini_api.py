import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import InvalidArgument, ResourceExhausted
from config import get_secret, set_secret

logger = logging.getLogger(__name__)


class GeminiAIProvider:
    """
    Provides an interface for interacting with the Google Gemini AI API.
    Handles API key management, model selection, conversation history,
    and error handling.
    """
    DEFAULT_MODEL = "gemini-1.5-flash"
    SUPPORTED_MODELS = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"]

    SAFETY_SETTINGS = [
        {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
        {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    ]

    def __init__(self):
        self._api_key = None
        self._model_name = self.DEFAULT_MODEL
        self._model = None
        logger.info("GeminiAIProvider initialized. Awaiting API key configuration.")

    def _initialize_model(self):
        """Initializes the GenerativeModel instance with current API key and model name."""
        if not self._api_key:
            self._model = None
            logger.warning("Cannot initialize Gemini model: API key is not set.")
            return

        try:
            self._model = genai.GenerativeModel(
                model_name=self._model_name,
                safety_settings=self.SAFETY_SETTINGS
            )
            logger.info(f"Gemini model '{self._model_name}' initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model '{self._model_name}': {e}")
            self._model = None
            raise RuntimeError(f"Failed to initialize Gemini model '{self._model_name}': {e}") from e

    def is_configured(self) -> bool:
        """Returns True if the API key and model are initialized."""
        return bool(self._api_key and self._model)

    def save_api_key_securely(self, api_key: str):
        """Securely stores the Gemini API key using the config module."""
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty.")
        set_secret("gemini_api_key", api_key.strip())
        logger.info("Gemini API key saved securely via config module.")

    def get_api_key_securely(self) -> str | None:
        """Retrieves the Gemini API key securely from the config module."""
        key = get_secret("gemini_api_key")
        if key:
            logger.debug("Gemini API key retrieved securely.")
        return key

    def set_api_key(self, api_key: str):
        """Configures the google.generativeai library with the provided API key."""
        if not api_key or not api_key.strip():
            self._api_key = None
            self._model = None
            genai.configure(api_key=None)
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
        """Sets the Gemini model to be used for generation."""
        if not model_name or not model_name.strip():
            raise ValueError("Model name cannot be empty.")
        clean_model = model_name.strip()
        if self._model_name != clean_model:
            self._model_name = clean_model
            if self._api_key:
                self._initialize_model()
            logger.info(f"Gemini model name updated to '{self._model_name}'.")

    def get_available_models(self) -> list[str]:
        """Fetches a list of available Gemini models that support generateContent."""
        if not self._api_key:
            logger.warning("Cannot get available models: API key is not set.")
            raise RuntimeError("Gemini API key is not set. Please configure it in settings.")
        try:
            models = genai.list_models()
            available_models = [
                m.name.replace("models/", "") for m in models
                if 'generateContent' in m.supported_generation_methods
            ]
            logger.info(f"Found {len(available_models)} available Gemini models.")
            return available_models
        except Exception as e:
            logger.exception("An error occurred while listing Gemini models.")
            raise RuntimeError(f"An error occurred while fetching models: {e}") from e

    def test_connection(self, model_name: str = None) -> bool:
        """
        Tests the connection to the Gemini API using the current or given model name.
        Returns True if successful, False otherwise.
        """
        if model_name:
            self.set_model(model_name)

        if not self._api_key or not self._model:
            logger.warning("Test connection failed: Provider not configured.")
            return False

        try:
            response = self._model.generate_content("Hello, respond with 'OK'.")
            return bool(response and response.text)
        except Exception as e:
            logger.error(f"Gemini test connection failed: {e}")
            return False

    def send_message(self, history: list, model_name: str = None) -> str:
        """
        Sends a conversation history to Gemini and returns the AI response string.
        """
        if model_name:
            self.set_model(model_name)

        if not self._api_key or not self._model:
            raise RuntimeError("Gemini API not configured. Please set your API key in Settings.")

        if not history:
            return "No input provided."

        try:
            chat_history = history[:-1] if len(history) > 1 else []
            latest_turn = history[-1]
            latest_prompt = latest_turn['parts'][0] if latest_turn.get('parts') else ""

            formatted_chat_history = []
            for item in chat_history:
                role = 'user' if item.get('role') in ('user', 'User') else 'model'
                text_part = item['parts'][0] if isinstance(item.get('parts'), list) else str(item.get('parts'))
                formatted_chat_history.append({'role': role, 'parts': [text_part]})

            chat = self._model.start_chat(history=formatted_chat_history)
            response = chat.send_message(latest_prompt)

            if response.text:ṭ
                return response.text.strip()

            if response.prompt_feedback and response.prompt_feedback.safety_ratings:
                feedback = ", ".join([f"{s.category.name}: {s.probability.name}"
                                      for s in response.prompt_feedback.safety_ratings])
                return f"I cannot respond to that due to safety guidelines. ({feedback})"

            return "I was unable to generate a response. Please try again."

        except InvalidArgument as e:
            logger.error(f"Gemini API Invalid Argument: {e}")
            raise ValueError(f"Invalid prompt or safety restriction: {e}") from e
        except ResourceExhausted as e:
            logger.error(f"Gemini API Quota Exceeded: {e}")
            raise RuntimeError("API quota or rate limit exceeded. Please try again later.") from e
        except Exception as e:
            logger.exception("An error occurred during Gemini message generation.")
            raise RuntimeError(f"Gemini Error: {e}") from e
