"""LLM Interfaces

Classes for interfacing with LLMs as defined in the `models` module.
"""
# ─── import statements ───────────────────────────────────────────────── ✦✦ ──

# standard library imports
import json
import logging
import os
import urllib.request
import urllib.parse
from datetime import datetime as dt
from pathlib import Path
from typing import Dict, List, Tuple, TYPE_CHECKING, Union
if TYPE_CHECKING:
    from _typeshed import SupportsWrite

# third-party imports
from dotenv import load_dotenv
from platformdirs import user_config_path

# local imports
from .models import (
    CHATGPT_CONVERSATIONS_DIR, CLAUDE_CONVERSATIONS_DIR,
    ClaudeModel, ChatGPTModel
)

# ─── logger setup ──────────────────────────────────────────────────────── ✦ ─
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ─── constants ─────────────────────────────────────────────────────────── ✦ ─
APP_NAME = "gnarly"
APP_AUTHOR = "k.lebryce"
APP_CONFIG_DIR: Path = user_config_path(
    APP_NAME, APP_AUTHOR, ensure_exists=True
)

# load environment variables from .env file
try:
    load_dotenv(Path(APP_CONFIG_DIR, ".env").resolve())
except FileNotFoundError:
    APP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    Path(APP_CONFIG_DIR, ".env").touch()
except IOError as e:
    raise IOError(
        "Failed to load environment variables from .env file."
    ) from e


# ─── interfaces ──────────────────────────────────────────────────────── ✦✦ ──
class Claude(ClaudeModel):
    def __init__(
        self,
        system_prompt: str = "You are Claude, a friendly AI assistant."
    ):
        super().__init__()
        self.api_key: str = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.conversation: List[Dict] = []
        self.max_tokens: int = 4096
        self.system_prompt = system_prompt
        self.temperature: float = 0.2
        
        # Ensure save_to is a Path object
        self.save_to = Path(CLAUDE_CONVERSATIONS_DIR) 
        
        # Create directory if it doesn't exist
        self.save_to.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Conversation will be saved to {self.save_to}")

    def message(self, msg: str) -> Tuple[Dict, Dict]:
        """
        Creates a payload using the `msg` string and returns Claude's
        response as a string.
        """
        self.conversation.append({"role": "user", "content": msg})

        # Prepare the API request
        url = "https://api.anthropic.com/v1/messages"
        
        data = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "temperature": self.temperature,
            "messages": self.conversation
        }
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Make the HTTP request
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"API request failed: {e.code} {e.reason} - {error_body}")
            raise Exception(f"Claude API error: {e.code} {e.reason}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

        # Extract response content
        response_content = result["content"][0]["text"]
        response = {"role": "assistant", "content": response_content}
        self.conversation.append(response)
        
        return response, result

    def save(self, save_as: Union[str, Path] = None) -> int:
        """
        Save the current conversation to a file.
        
        Args:
            save_as: Optional path to save the conversation. If not provided,
                    uses the default path from initialization.
                    
        Returns:
            0 on success, 1 on failure
        """
        try:
            target_path = Path(save_as) if save_as else self.save_to
            if not target_path.is_absolute():
                target_path = Path(CLAUDE_CONVERSATIONS_DIR) / target_path
                
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, "w") as f:
                json.dump(self.conversation, f, indent=4)
            logger.info(f"Successfully saved conversation to {target_path}")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {str(e)}")
            return 1

class ChatGPT(ChatGPTModel):
    """A turn-based, chat-like interface for the OpenAI API via HTTP requests.

    This class's attributes are automatically defined on instantiation.

    Attributes:
      api_key:
        A string representing the OpenAI API key.
      conversation:
        A list of dictionaries representing each message exchanged
        with ChatGPT over the course of the instance's lifetime.
      model:
        A string representing the ChatGPT model to be called on
        invocation of the `message` method.
      max_tokens:
        An integer representing the maximum number of tokens that
        the model should output.
      save_to:
        A `Path` object representing the directory to which the
        contents of the `conversation` attribute should be written.
      temperature:
        A float representing the degree of "randomness" that the model
        should leverage in generating its response.
    """

    def __init__(
        self,
        model: str = "gpt-4",
        instructions: str = "You are ChatGPT, a helpful AI assistant."
    ) -> None:
        """Initialize a `ChatGPT` instance.
        
        Args:
          model (str):
            A string representing the ChatGPT model to be called.
            Defaults to "gpt-4".
          instructions (str):
            A string representing the system prompt to be used.
            Defaults to "You are ChatGPT, a helpful AI assistant.".

        Returns:
            `None`.
        """
        super().__init__()
        self.api_key: str = self.api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.conversation: List[Dict] = []
        self.model: str = model
        self.instructions: str = instructions
        self.max_tokens: int = 4096
        self.save_to: Path = Path(CHATGPT_CONVERSATIONS_DIR)
        self.temperature: float = 0.2
        
        # Ensure that the conversations directory exists.
        self.save_to.parent.mkdir(parents=True, exist_ok=True)

    def message(self, msg: str) -> str:
        """Send a message to ChatGPT.

        This method calls OpenAI's Chat Completions API via HTTP request.

        Args:
            msg: A string representing the message to be sent.

        Returns:
            The response text from ChatGPT.
        """
        self.conversation.append({"role": "user", "content": msg})
        
        # Prepare messages for API call
        messages = [{"role": "system", "content": self.instructions}] + self.conversation
        
        # Prepare the API request
        url = "https://api.openai.com/v1/chat/completions"
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Make the HTTP request
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"API request failed: {e.code} {e.reason} - {error_body}")
            raise Exception(f"OpenAI API error: {e.code} {e.reason}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

        # Extract response content
        response_text = result["choices"][0]["message"]["content"]
        response = {"role": "assistant", "content": response_text}
        self.conversation.append(response)

        return response_text

    def save(
        self,
        save_as: Union[str, Path] = None
    ) -> int:
        """Save the current conversation to a file.
        
        Args:
            save_as: Optional path to save the conversation.
                    
        Returns:
            0 on success, 1 on failure
        """
        if save_as is None:
            save_as = Path(
                f"~/.llm/chatgpt/conversations/{dt.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
            ).expanduser()
        
        try:
            target_path = Path(save_as)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, "w") as f:
                logger.info(f"Saving conversation to {target_path}")
                json.dump(self.conversation, f, indent=4)
                logger.info("Success.")
                return 0
        except Exception as e:
            logger.error(f"Error: Failed to save conversation: {str(e)}")
            return 1
