"""LLM Interfaces

Classes for interfacing with LLMs as defined in the `models` module.
"""
# ─── import statements ───────────────────────────────────────────────── ✦✦ ──

# standard library imports
import json
import logging
import os
from datetime import datetime as dt
from pathlib import Path
from typing import Dict, List, Tuple, TYPE_CHECKING, Union
if TYPE_CHECKING:
    from _typeshed import SupportsWrite

# third-party imports
from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv
from openai import OpenAI
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
APP_NAME = "cleft"
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
        self.client: Anthropic = Anthropic()
        self.conversation: List[Dict] = []
        self.max_tokens: int = 4096
        self.system_prompt = system_prompt
        self.temperature: float = 0.2
        
        # Ensure save_to is a Path object
        self.save_to = Path(CLAUDE_CONVERSATIONS_DIR) 
        
        # Create directory if it doesn't exist
        self.save_to.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Conversation will be saved to {self.save_to}")

    def message(self, msg: str) -> Tuple[Dict, Message]:
        """
        Creates a payload using the `msg` string and returns Claude's
        response as a string.
        """
        self.conversation.append({"role": "user", "content": msg})

        # Call the Anthropic API.
        result = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            temperature=self.temperature,
            messages=self.conversation
        )

        response = {"role": "assistant", "content": result.content[0].text}
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
    """A turn-based, chat-like interface for the OpenAI Python SDK.

    This class's attributes are automatically defined on instantiation.

    Attributes:
      client:
        An `openai.OpenAI` instance.
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
        A float representing the degree of 'randomness' that the model
        should leverage in generating its response.
    """

    def __init__(
        self,
        model: str = "gpt-4.1",
        instructions: str = "You are ChatGPT, a helpful AI assistant."
    ) -> None:
        """Initialize a `ChatGPT` instance.
        
        Args:
          model (str):
            A string representing the ChatGPT model to be called.
            Defaults to "gpt-4.1".
          system_prompt (str):
            A string representing the system prompt to be used.
            Defaults to 'You are ChatGPT, a helpful AI assistant.'.

        Returns:
            `None`.
        """
        self.client = OpenAI()
        self.conversation: List[Dict] = []
        self.model: str = model
        self.instructions: str = instructions
        self.max_tokens: int = 4096
        self.save_to: Path = Path(CHATGPT_CONVERSATIONS_DIR)
        self.temperature: float = 0.2
        
        # Ensure that the conversations directory exists.
        self.save_to.parent.mkdir(parents=True, exist_ok=True)

    def message(self, msg: str):
        """Send a message to ChatGPT.

        This method calls OpenAI's `Responses` API, passing either
        `msg` or the text output of the last response received as the
        `OpenAI.responses.create` method's `input` parameter. Upon
        receipt, the resulting `Response` object is appended to
        `self.conversation`.

        Args:
            msg: A string representing the message to be sent.

        Returns:
            Nothing.
        """
        self.conversation.append({"role": "user", "content": msg})
        
        # Call the OpenAI API.
        if hasattr(self, "response"):
            self.response = self.client.responses.create(
                model=self.model,
                previous_response_id=self.response.id,
                instructions=self.instructions,
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
                input=msg
            )
        else:
            self.response = self.client.responses.create(
                model=self.model,
                instructions=self.instructions,
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
                input=msg
            )

        response_text = {"role": "assistant", "content": self.response.output_text}

        self.conversation.append(response_text)

        return self.response.output_text 

    # noinspection DuplicatedCode
    def save(
        self,
        save_as: Union[str, Path] = (
            Path(
                f"~/.llm/chatgpt/conversations/\
                {dt.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
            ).expanduser()
        )
    ) -> int:
        with open(save_as, "w") as f:
            f: SupportsWrite[str]
            logger.info(f"Saving conversation to {self.save_to}")

            try:
                json.dump(self.conversation, f, indent=4)
                logger.info("Success.")
                return 0
            except Exception as e:
                raise Exception("Error: Failed to save conversation.") from e
                return 1
