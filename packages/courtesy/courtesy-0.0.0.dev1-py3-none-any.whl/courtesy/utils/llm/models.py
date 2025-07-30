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
from dotenv import load_dotenv


# Set up logging.
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Create LLM data directories as needed.
courtesy_dir = Path("~/Library/Mobile Documents/com~apple~CloudDocs/courtesy").expanduser()
llm_directory = courtesy_dir / "llm"
dotenv_path = courtesy_dir / ".env"
if not courtesy_dir.exists():
    courtesy_dir.mkdir(parents=True, exist_ok=True)
if not llm_directory.exists():
    llm_directory.mkdir(parents=True, exist_ok=True)
if not dotenv_path.exists():
    dotenv_path.touch(exist_ok=True)


# Load environment variables.
load_dotenv(dotenv_path)


# Getting API keys from environment - masked for security
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# Get LLM conversation directories.
CLAUDE_CONVERSATIONS_DIR = Path(
    os.getenv(
        "CLAUDE_CONVERSATIONS_DIR",
        str(llm_directory / "claude/conversations")
    )
)

CHATGPT_CONVERSATIONS_DIR = Path(
    os.getenv(
        "CHATGPT_CONVERSATIONS_DIR",
        str(llm_directory / "chatgpt/conversations")
    )
)


class LLM(Protocol):
    """
    Protocol defining the attributes required for LLM conformance.
    
    Attributes
    ----------
    api_key : str
        The API key for the LLM service.
    name : str
        The name of the LLM model.
    """

    api_key: str
    name: str


@dataclass
class ClaudeModel:
    """
    Data class representing a Claude model configuration.
    
    Parameters
    ----------
    api_key : str, optional
        The Anthropic API key. Retrieved from environment if not provided.
    model : str, optional
        The Claude model identifier, by default "claude-3-5-sonnet-20241022".
    name : str, optional
        The model name, by default "Claude".
    
    Attributes
    ----------
    api_key : str
        The Anthropic API key.
    model : str
        The Claude model identifier.
    name : str  
        The model name.
    """
    api_key: str = ""  # Will be set from environment in __post_init__
    model: str = "claude-3-5-sonnet-20241022"
    name: str = "Claude"
    
    def __post_init__(self):
        """Initialize API key from environment if not provided."""
        if not self.api_key:
            self.api_key = ANTHROPIC_API_KEY

    @staticmethod
    def load_conversation(filepath: Union[str, Path]) -> List[Dict[str, str]]:
        """
        Load a previous conversation from a JSON file.

        Parameters
        ----------
        filepath : Union[str, Path]
            Path to the conversation JSON file. If relative, will be resolved
            relative to the Claude conversations directory.

        Returns
        -------
        List[Dict[str, str]]
            List of message dictionaries containing the conversation history.
            Each dictionary has 'role' and 'content' keys.

        Raises
        ------
        FileNotFoundError
            If the specified file doesn't exist.
        json.JSONDecodeError
            If the file contains invalid JSON.
        ValueError
            If the conversation format is invalid.
        
        Examples
        --------
        >>> messages = ClaudeModel.load_conversation("my_chat.json")
        >>> print(len(messages))
        5
        """
        filepath = Path(filepath)
        if not filepath.is_absolute():
            filepath = Path(CLAUDE_CONVERSATIONS_DIR) / filepath

        if not filepath.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.touch(exist_ok=True)

        try:
            with open(filepath, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                conversation = json.loads(content)

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
    """
    Data class representing a ChatGPT model configuration.
    
    Parameters
    ----------
    api_key : str, optional
        The OpenAI API key. Retrieved from environment if not provided.
    model : str, optional
        The GPT model identifier, by default "gpt-4".
    name : str, optional
        The model name, by default "ChatGPT".
    
    Attributes
    ----------
    api_key : str
        The OpenAI API key.
    model : str
        The GPT model identifier.
    name : str
        The model name.
    """
    api_key: str = ""  # Will be set from environment in __post_init__
    model: str = "gpt-4"
    name: str = "ChatGPT"
    
    def __post_init__(self):
        """Initialize API key from environment if not provided."""
        if not self.api_key:
            self.api_key = OPENAI_API_KEY

    @staticmethod
    def load_conversation(filepath: Union[str, Path]) -> List[Dict[str, str]]:
        """
        Load a previous conversation from a JSON file.

        Parameters
        ----------
        filepath : Union[str, Path]
            Path to the conversation JSON file. If relative, will be resolved
            relative to the ChatGPT conversations directory.

        Returns
        -------
        List[Dict[str, str]]
            List of message dictionaries containing the conversation history.
            Each dictionary has 'role' and 'content' keys.

        Raises
        ------
        FileNotFoundError
            If the specified file doesn't exist.
        json.JSONDecodeError
            If the file contains invalid JSON.
        ValueError
            If the conversation format is invalid.
        
        Examples
        --------
        >>> messages = ChatGPTModel.load_conversation("my_chat.json")
        >>> print(len(messages))
        3
        """
        filepath = Path(filepath)
        if not filepath.is_absolute():
            filepath = Path(CHATGPT_CONVERSATIONS_DIR) / filepath

        if not filepath.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.touch(exist_ok=True)

        try:
            with open(filepath, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                conversation = json.loads(content)

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
