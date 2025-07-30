"""
Large Language Model (LLM) implementations for pdf2podcast.
"""

import os
import re
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from dotenv import load_dotenv

from langchain.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core import retry
from google.api_core.exceptions import GoogleAPIError
from .base import BaseLLM
from .prompts import PodcastPromptBuilder
from .parsers import PodcastParser, StrictDialoguePodcastParser

# Setup logging
logger = logging.getLogger(__name__)


def retry_on_exception(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (GoogleAPIError,),
) -> Callable:
    """
    Retry decorator with exponential backoff.

    Args:
        retries (int): Maximum number of retries
        delay (float): Initial delay between retries in seconds
        backoff (float): Backoff multiplier
        exceptions (tuple): Exceptions to catch
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_delay = delay
            last_exception = None

            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if i < retries - 1:
                        logger.warning(
                            f"Attempt {i + 1}/{retries} failed: {str(e)}. "
                            f"Retrying in {retry_delay:.1f}s..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= backoff
                    else:
                        logger.error(f"All {retries} attempts failed.")

            raise last_exception

        return wrapper

    return decorator


class GeminiLLM(BaseLLM):
    """
    Google's Gemini-based LLM implementation with optimized content generation.
    """

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "gemini-1.5-flash",
        language: str = "en",
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_output_tokens: int = 4096,
        streaming: bool = False,
        prompt_builder: PodcastPromptBuilder = None,
        dialogue: bool = False,
    ):
        """
        Initialize Gemini LLM system.

        Args:
            api_key (str, optional): Google API key. If not provided, will look for GENAI_API_KEY env var
            model_name (str): Name of the Gemini model to use (default: "gemini-1.5-flash")
            temperature (float): Sampling temperature (default: 0.2)
            top_p (float): Nucleus sampling parameter (default: 0.9)
            max_output_tokens (int): Maximum output length (default: 4096)
            streaming (bool): Whether to use streaming mode (default: False)
            prompt_builder (Optional[PodcastPromptBuilder]): Custom prompt builder
            dialogue (bool): Whether to generate dialogue between speakers (default: False)
        """
        super().__init__(prompt_builder)

        if api_key is None:
            load_dotenv()
            api_key = os.getenv("GENAI_API_KEY")
            if not api_key:
                raise ValueError("No API key provided and GENAI_API_KEY not found")

        self.language = language
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            streaming=streaming,
            google_api_key=api_key,
        )

    def _clean_text(self, text: str) -> str:
        """
        Clean text using regex patterns to remove visual references and formatting.

        Args:
            text (str): Input text to clean

        Returns:
            str: Cleaned text with visual references removed
        """
        patterns = [
            r"(Figure|Fig\.|Table|Image)\s+\d+[a-z]?",
            r"(shown|illustrated|depicted|as seen) (in|on|above|below)",
            r"(refer to|see|view) (figure|table|image)",
            r"\(fig\.\s*\d+\)",
            r"as (shown|depicted) (here|below|above)",
        ]

        processed = text
        for pattern in patterns:
            processed = re.sub(pattern, "", processed, flags=re.IGNORECASE)

        processed = re.sub(r"\s+", " ", processed)
        return processed.strip()

    @retry_on_exception()
    def generate_podcast_script(
        self,
        text,
        **kwargs: Dict[str, Any],
    ) -> str:
        """
        Generate a coherent podcast script.

        Args:
            **kwargs: Additional parameters for customization, including:
                - text (str): Input text to convert into a podcast script
                - dialogue (bool): Whether to generate dialogue between speakers
                - query (str): Optional query to guide content generation
                - instructions (str): Optional additional instructions for generation

        Returns:
            str: Generated podcast script
        """
        try:
            # Clean and validate input text
            if not text or not text.strip():
                raise ValueError("Input text cannot be empty")

            processed_text = self._clean_text(text)
            if not processed_text:
                raise ValueError("Text cleaning resulted in empty content")

            dialogue = kwargs.get("dialogue", False)
            print(f"Dialogue: {dialogue}")

            # Generate initial script
            try:
                # Create a prompt builder
                if self.prompt_builder is None:
                    prompt_builder = PodcastPromptBuilder(dialogue=dialogue)
                else:
                    # If we have a custom prompt builder, use it as is
                    prompt_builder = self.prompt_builder

                # Get the prompt template with language
                prompt_template = prompt_builder.build_prompt(
                    text=processed_text,
                    **kwargs,
                )

                # Create the chain based on format
                logger.info("Creating podcast chain...")
                # Use strict parser for better reliability when dialogue is requested
                if dialogue:
                    parser = StrictDialoguePodcastParser()
                    logger.info(
                        "Using StrictDialoguePodcastParser for guaranteed dialogue format"
                    )
                else:
                    parser = PodcastParser()
                    logger.info("Using standard PodcastParser for text format")

                # Create chain with properly formatted prompt and format variables
                chain = prompt_template | self.llm | parser

                # Get format instructions from the selected parser
                format_instructions = parser.get_format_instructions()

                # Build input variables based on template requirements
                input_variables = {
                    "text": processed_text,
                    "query": kwargs.get("query", ""),
                    "format_instructions": format_instructions,
                    "language": self.language,
                }

                # Only add instructions if the template expects them (not pre-filled)
                if "instructions" in prompt_template.input_variables:
                    input_variables["instructions"] = kwargs.get("instructions", "")

                result = chain.invoke(input_variables)

                logger.info("Successfully generated script")
                return result.model_dump_json()

            except GoogleAPIError as e:
                logger.error(f"Google API error: {str(e)}")
                raise  # Will be caught by retry decorator
            except Exception as e:
                logger.error(f"Unexpected error in script generation: {str(e)}")
                raise Exception(f"Failed to generate podcast script: {str(e)}")

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise
