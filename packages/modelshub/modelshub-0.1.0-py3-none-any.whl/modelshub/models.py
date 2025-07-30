import os
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
from langchain.chat_models.base import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic

class BaseLLM(ABC):
    """Base class for all LLM implementations."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """Initialize the LLM.
        
        Args:
            api_key: API key for the LLM provider
            model_name: Name of the model to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the LLM
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        self._model = self._initialize_model()
    
    @abstractmethod
    def _initialize_model(self) -> BaseChatModel:
        """Initialize the underlying LLM model."""
        pass
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate text from the LLM.
        
        Args:
            prompt: The prompt to generate from
            temperature: Override the default temperature
            max_tokens: Override the default max tokens
            **kwargs: Additional arguments to pass to the LLM
            
        Returns:
            The generated text
        """
        messages = [{"role": "user", "content": prompt}]
        response = self._model.invoke(
            messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **{**self.kwargs, **kwargs}
        )
        return response.content
    
    def chat(
        self,
        messages: list[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Chat with the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Override the default temperature
            max_tokens: Override the default max tokens
            **kwargs: Additional arguments to pass to the LLM
            
        Returns:
            The generated response
        """
        response = self._model.invoke(
            messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **{**self.kwargs, **kwargs}
        )
        return response.content

class Gemini(BaseLLM):
    """Google Gemini LLM implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """Initialize Gemini LLM.
        
        Args:
            api_key: Google API key. If not provided, will look for GOOGLE_API_KEY env var
            model_name: Name of the Gemini model to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the LLM
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key must be provided or set as GOOGLE_API_KEY environment variable")
        
        super().__init__(
            api_key=self.api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def _initialize_model(self) -> ChatGoogleGenerativeAI:
        """Initialize the Gemini model."""
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            **self.kwargs
        )

class OpenAI(BaseLLM):
    """OpenAI LLM implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """Initialize OpenAI LLM.
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY env var
            model_name: Name of the OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the LLM
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        super().__init__(
            api_key=self.api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def _initialize_model(self) -> ChatOpenAI:
        """Initialize the OpenAI model."""
        return ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **self.kwargs
        )

class Groq(BaseLLM):
    """Groq LLM implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """Initialize Groq LLM.
        
        Args:
            api_key: Groq API key. If not provided, will look for GROQ_API_KEY env var
            model_name: Name of the Groq model to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the LLM
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key must be provided or set as GROQ_API_KEY environment variable")
        
        super().__init__(
            api_key=self.api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def _initialize_model(self) -> ChatGroq:
        """Initialize the Groq model."""
        return ChatGroq(
            model_name=self.model_name,
            groq_api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **self.kwargs
        )

class Anthropic(BaseLLM):
    """Anthropic Claude LLM implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """Initialize Anthropic LLM.
        
        Args:
            api_key: Anthropic API key. If not provided, will look for ANTHROPIC_API_KEY env var
            model_name: Name of the Anthropic model to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the LLM
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key must be provided or set as ANTHROPIC_API_KEY environment variable")
        
        super().__init__(
            api_key=self.api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def _initialize_model(self) -> ChatAnthropic:
        """Initialize the Anthropic model."""
        return ChatAnthropic(
            model_name=self.model_name,
            anthropic_api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **self.kwargs
        ) 