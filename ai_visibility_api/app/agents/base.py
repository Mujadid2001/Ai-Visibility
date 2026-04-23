"""Base agent class."""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import os

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, provider: str = None):
        """Initialize agent with AI provider.
        
        Args:
            provider: 'openai' or 'anthropic'
        """
        self.provider = provider or os.getenv("AI_PROVIDER", "openai")
        self.client = self._init_client()
    
    def _init_client(self):
        """Initialize the AI client based on provider."""
        if self.provider == "openai":
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            return OpenAI(api_key=api_key)
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            return Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling malformed output.
        
        Args:
            response_text: Raw response from LLM
        
        Returns:
            Parsed JSON as dictionary
        
        Raises:
            ValueError: If JSON cannot be parsed
        """
        try:
            # Try direct parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end > start:
                    json_str = response_text[start:end].strip()
                    return json.loads(json_str)
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end > start:
                    json_str = response_text[start:end].strip()
                    return json.loads(json_str)
            
            # Last resort: look for JSON object/array pattern
            import re
            json_match = re.search(r'\{.*\}|\[.*\]', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            raise ValueError(f"Could not parse JSON from response: {response_text[:200]}")
    
    def call_llm(self, system_prompt: str, user_message: str, json_mode: bool = True) -> str:
        """Call the LLM with given prompts.
        
        Args:
            system_prompt: System context for the agent
            user_message: User message/query
            json_mode: Whether to request JSON output
        
        Returns:
            LLM response text
        """
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"} if json_mode else None,
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_message},
                    ],
                )
                return response.content[0].text
        
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """Run the agent. Must be implemented by subclasses."""
        pass
