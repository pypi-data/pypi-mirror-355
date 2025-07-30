"""
LLM Models
==========

Classes for representing LLM models and their characteristic attributes.

"""

# Standard library imports: Package-level
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Protocol, Union

# Third-party imports: Module-level
from anthropic import Anthropic
from dotenv import load_dotenv


# Set up logging.
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Create LLM data directories as needed.
cleft_dir = Path("~/Library/Mobile Documents/com~apple~CloudDocs/cleft").expanduser()
llm_directory = cleft_dir / "llm"
dotenv_path = cleft_dir / ".env"
if not cleft_dir.exists:
    cleft_dir.mkdir(parents=True, exist_ok=True)
if not llm_directory.exists():
    llm_directory.mkdir(parents=True, exist_ok=True)
if not dotenv_path.exists():
    dotenv_path.touch(exist_ok=True)


# Load environment variables.
load_dotenv(dotenv_path)


# Getting API keys from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Get LLM conversation directories.
CLAUDE_CONVERSATIONS_DIR = os.getenv(
    "CLAUDE_CONVERSATIONS_DIR", str(llm_directory / "claude/conversations")
)
CHATGPT_CONVERSATIONS_DIR = os.getenv(
    "CHATGPT_CONVERSATIONS_DIR", str(llm_directory / "chatgpt/conversations")
)


if not Path(CLAUDE_CONVERSATIONS_DIR).exists():
    try:
        Path(CLAUDE_CONVERSATIONS_DIR).mkdir()
    except FileExistsError as e:
        raise (f"ERROR: The file `{CLAUDE_CONVERSATIONS_DIR}` already exists.")
    else:
        logger.info(f"Successfully created `{CLAUDE_CONVERSATIONS_DIR}`.")

if not Path(CHATGPT_CONVERSATIONS_DIR).exists():
    try:
        Path(CHATGPT_CONVERSATIONS_DIR).mkdir()
    except FileExistsError as e:
        raise (f"ERROR: The file `{CHATGPT_CONVERSATIONS_DIR}` already exists.")
    else:
        logger.info(f"Successfully created `{CHATGPT_CONVERSATIONS_DIR}`.")


class LLM(Protocol):
    """
    Defines the attributes required for conformance to the LLM protocol.
    """

    api_key: str
    name: str


@dataclass
class ClaudeModel:
    api_key: str = ANTHROPIC_API_KEY
    model: str = "claude-3-7-sonnet-latest"
    name: str = "Claude"

    @staticmethod
    def load_conversation(filepath: Union[str, Path]) -> List[Dict[str, str]]:
        """
        Load a previous conversation from a JSON file in the conversations directory.

        Args:
            filepath: Path to the conversation JSON file

        Returns:
            List of message dictionaries containing the conversation history

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            JSONDecodeError: If the file contains invalid JSON
        """
        filepath = Path(filepath)
        if not filepath.is_absolute():
            filepath = Path(CLAUDE_CONVERSATIONS_DIR) / filepath

        if not filepath.exists():
            filepath.touch(exist_ok=True)

        try:
            with open(filepath, "r") as f:
                conversation = json.load(f)

            # Validate conversation format
            if not isinstance(conversation, list):
                raise ValueError("Conversation must be a list of messages")

            for msg in conversation:
                if (
                    not isinstance(msg, dict)
                    or "role" not in msg
                    or "content" not in msg
                ):
                    raise ValueError("Invalid message format in conversation")

            return conversation

        except FileNotFoundError:
            logger.error(f"Conversation file not found: {filepath}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in conversation file: {filepath}")
            raise
        except Exception as e:
            logger.error(f"Error loading conversation: {str(e)}")
            raise


@dataclass
class ChatGPTModel:
    api_key: str = OPENAI_API_KEY
    model: str = "gpt-4.1"
    name: str = "ChatGPT"

    @staticmethod
    def load_conversation(filepath: Union[str, Path]) -> List[Dict[str, str]]:
        """
        Load a previous conversation from a JSON file in the conversations directory.

        Args:
            filepath: Path to the conversation JSON file

        Returns:
            List of message dictionaries containing the conversation history

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            JSONDecodeError: If the file contains invalid JSON
        """
        filepath = Path(filepath)
        if not filepath.is_absolute():
            filepath = Path(CHATGPT_CONVERSATIONS_DIR) / filepath

        if not filepath.exists():
            filepath.touch(exist_ok=True)

        try:
            with open(filepath, "r") as f:
                conversation = json.load(f)

            # Validate conversation format
            if not isinstance(conversation, list):
                raise ValueError("Conversation must be a list of messages")

            for msg in conversation:
                if (
                    not isinstance(msg, dict)
                    or "role" not in msg
                    or "content" not in msg
                ):
                    raise ValueError("Invalid message format in conversation")

            return conversation

        except FileNotFoundError:
            logger.error(f"Conversation file not found: {filepath}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in conversation file: {filepath}")
            raise
        except Exception as e:
            logger.error(f"Error loading conversation: {str(e)}")
            raise
