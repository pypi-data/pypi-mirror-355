"""
LLM Interfaces
==============

Dependency-free interfaces for LLM interaction.

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
from typing import Dict, List, Tuple, Union

# local imports
from .models import (
    CHATGPT_CONVERSATIONS_DIR, CLAUDE_CONVERSATIONS_DIR,
    ClaudeModel, ChatGPTModel
)

# ─── logger setup ──────────────────────────────────────────────────────── ✦ ─
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ─── interfaces ──────────────────────────────────────────────────────── ✦✦ ──
class Claude(ClaudeModel):
    """
    Interface for interacting with Claude AI via the Anthropic API.
    
    This class provides a conversational interface to Claude, maintaining
    conversation history and handling API communication.
    
    Parameters
    ----------
    system_prompt : str, optional
        The system prompt to use for conversations, by default 
        "You are Claude, a friendly AI assistant."
    
    Attributes
    ----------
    api_key : str
        The Anthropic API key retrieved from environment variables.
    conversation : List[Dict]
        List of conversation messages with 'role' and 'content' keys.
    max_tokens : int
        Maximum number of tokens for responses, by default 4096.
    system_prompt : str
        The system prompt used for conversations.
    temperature : float
        Sampling temperature for response generation, by default 0.2.
    save_to : Path
        Directory path where conversations are saved.
    
    Raises
    ------
    ValueError
        If ANTHROPIC_API_KEY environment variable is not set.
    
    Examples
    --------
    >>> claude = Claude()
    >>> response, full_result = claude.message("Hello!")
    >>> print(response['content'])
    Hello! How can I help you today?
    """
    
    def __init__(
        self,
        system_prompt: str = "You are Claude, a friendly AI assistant."
    ):
        super().__init__()
        self._api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self._api_key:
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
    
    @property
    def api_key(self) -> str:
        """
        Get the full API key for actual usage.
        
        Returns
        -------
        str
            The complete API key.
        """
        return getattr(self, '_api_key', '')

    @api_key.setter
    def api_key(self, value: str) -> None:
        """
        Set the full API key for actual usage.

        Returns
        -------
        None
        """
        self._api_key = value
    
    @property
    def api_key_masked(self) -> str:
        """
        Get the API key masked for display/documentation.
        
        Returns
        -------
        str
            Masked API key string showing only last 4 characters.
        """
        if hasattr(self, '_api_key') and self._api_key:
            return f"sk-...{self._api_key[-4:]}" if len(self._api_key) > 4 else "***"
        return ""

    @api_key_masked.setter
    def api_key_masked(self, value: str) -> None:
        """
        Set the masked API key for display/documentation.

        Returns
        -------
        None
        """
        self._api_key_masked = value

    def message(self, msg: str) -> Tuple[Dict, Dict]:
        """
        Send a message to Claude and get a response.
        
        Parameters
        ----------
        msg : str
            The message to send to Claude.
            
        Returns
        -------
        Tuple[Dict, Dict]
            A tuple containing:
            - response: Dict with 'role' and 'content' keys
            - full_result: Complete API response dictionary
            
        Raises
        ------
        Exception
            If the API request fails or returns an error.
            
        Examples
        --------
        >>> claude = Claude()
        >>> response, result = claude.message("What is 2+2?")
        >>> print(response['content'])
        2 + 2 = 4
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
            "x-api-key": self._api_key,
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
        Save the current conversation to a JSON file.
        
        Parameters
        ----------
        save_as : Union[str, Path], optional
            Path to save the conversation. If not provided, uses the default
            path from initialization. Relative paths are resolved relative
            to the Claude conversations directory.
            
        Returns
        -------
        int
            0 on success, 1 on failure.
            
        Examples
        --------
        >>> claude = Claude()
        >>> claude.message("Hello")
        >>> result = claude.save("my_conversation.json")
        >>> print(result)
        0
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
    """
    A turn-based, chat-like interface for the OpenAI API.

    This class provides a conversational interface to ChatGPT models,
    maintaining conversation history and handling API communication
    via HTTP requests.

    Parameters
    ----------
    model : str, optional
        The ChatGPT model identifier to use, by default "gpt-4".
    instructions : str, optional
        The system prompt/instructions for the model, by default
        "You are ChatGPT, a helpful AI assistant.".

    Attributes
    ----------
    api_key : str
        The OpenAI API key retrieved from environment variables.
    conversation : List[Dict]
        List of message dictionaries representing the conversation history.
        Each message has 'role' and 'content' keys.
    model : str
        The ChatGPT model identifier.
    instructions : str
        The system instructions/prompt.
    max_tokens : int
        Maximum number of tokens for model output, by default 4096.
    save_to : Path
        Directory path where conversations are saved.
    temperature : float
        Sampling temperature for response randomness, by default 0.2.
        
    Raises
    ------
    ValueError
        If OPENAI_API_KEY environment variable is not set.
        
    Examples
    --------
    >>> chatgpt = ChatGPT(model="gpt-4", instructions="You are a helpful assistant.")
    >>> response = chatgpt.message("Hello!")
    >>> print(response)
    Hello! How can I help you today?
    """

    def __init__(
        self,
        model: str = "gpt-4",
        instructions: str = "You are ChatGPT, a helpful AI assistant."
    ) -> None:
        super().__init__()
        self._api_key = self.api_key or os.getenv("OPENAI_API_KEY", "")
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.conversation: List[Dict] = []
        self.model: str = model
        self.instructions: str = instructions
        self.max_tokens: int = 4096
        self.save_to: Path = Path(CHATGPT_CONVERSATIONS_DIR)
        self.temperature: float = 0.2
        
        # Ensure that the conversations directory exists.
        self.save_to.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def api_key(self) -> str:
        """
        Get the full API key for actual usage.
        
        Returns
        -------
        str
            The complete API key.
        """
        return getattr(self, '_api_key', '')

    @api_key.setter
    def api_key(self, value: str) -> None:
        """
        Set the full API key for actual usage.

        Returns
        -------
        str
            The complete API key.
        """
        self._api_key = value
    
    @property
    def api_key_masked(self) -> str:
        """
        Get the API key masked for display/documentation.
        
        Returns
        -------
        str
            Masked API key string showing only last 4 characters.
        """
        if hasattr(self, '_api_key') and self._api_key:
            return f"sk-...{self._api_key[-4:]}" if len(self._api_key) > 4 else "***"
        return ""

    @api_key_masked.setter
    def api_key_masked(self, value: str) -> None:
        """
        Set the masked API key string.

        Returns
        -------
        None
        """
        self._api_key_masked = value

    def message(self, msg: str) -> str:
        """
        Send a message to ChatGPT and get a response.

        This method calls OpenAI's Chat Completions API via HTTP request.

        Parameters
        ----------
        msg : str
            The message to be sent to ChatGPT.

        Returns
        -------
        str
            The response text from ChatGPT.
            
        Raises
        ------
        Exception
            If the API request fails or returns an error.
            
        Examples
        --------
        >>> chatgpt = ChatGPT()
        >>> response = chatgpt.message("What is the capital of France?")
        >>> print(response)
        The capital of France is Paris.
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
            "Authorization": f"Bearer {self._api_key}",
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
        """
        Save the current conversation to a JSON file.
        
        Parameters
        ----------
        save_as : Union[str, Path], optional
            Path to save the conversation. If not provided, generates
            a timestamped filename in the default conversations directory.
                    
        Returns
        -------
        int
            0 on success, 1 on failure.
            
        Examples
        --------
        >>> chatgpt = ChatGPT()
        >>> chatgpt.message("Hello")
        >>> result = chatgpt.save("my_conversation.json")
        >>> print(result)
        0
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
