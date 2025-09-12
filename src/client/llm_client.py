import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        self.model_name = self._get_default_model()
        
        self.model = self._initialize_model()

    def _get_default_model(self) -> str:
        defaults = {
            "openai": "gpt-4",
            "anthropic": "claude-3-sonnet-20240229", 
            "google": "gemini-2.0-flash"
        }
        return defaults.get(self.provider, "gpt-4")

    def _initialize_model(self):

        timeout = float(os.getenv("LLM_TIMEOUT", "5"))
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))

        match self.provider:
            case "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable is required")
                return ChatOpenAI(
                    model=self.model_name,
                    api_key=api_key,
                    temperature=0.7,
                    request_timeout=timeout,
                    max_retries=max_retries
                )
                
            case "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY") 
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable is required")
                return ChatAnthropic(
                    model=self.model_name,
                    api_key=api_key,
                    temperature=0.7,
                    timeout=timeout,
                    max_retries=max_retries
                )
                
            case "google":
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY environment variable is required") 
                return ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=api_key,
                    temperature=0.7,
                    timeout=timeout,
                    max_retries=max_retries
                )
            case _:
                raise ValueError(f"Provider '{self.provider}' not supported. Use: openai, anthropic, google")

    def generate_text(self, prompt: str) -> AIMessage:
        return self.model.invoke([HumanMessage(content=prompt)])