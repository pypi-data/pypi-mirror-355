from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal, Any, Dict
import os
import dspy

class LLMSpec(BaseModel):
    """
    Light-weight serialisable config for a language model
    compatible with DSPy / LiteLLM.
    """

    # Identification
    name: str                                   # e.g. "gpt-4o-mini", "anthropic/claude-3-sonnet"
    model_type: Literal["chat", "text"] = "chat"
    provider: Literal["openai", "anthropic", "mistral", "azure_openai",
                      "ollama", "local", "other"] | None = None

    # Generation parameters
    temperature: float = 0.0                    # 0‒2
    max_tokens: Optional[int] = None            # None → provider default
    stop: str | List[str] | None = None

    # Runtime behaviour
    cache: bool = True
    num_retries: int = 3

    # Networking / auth
    api_key_env: Optional[str] = "OPENAI_API_KEY"
    api_base_url: Optional[str] = None

    # Fine-tuning
    finetuning_model: Optional[str] = None

    # Arbitrary extra args forwarded to LiteLLM
    extra: Dict[str, Any] = Field(default_factory=dict)

    # ­­­­­­­­­­­­­­­­­ validation ­­­­­­­­­­­­­­­­
    @model_validator(mode="after")
    def _check_values(self):
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")

        # coerce stop into list[str] if user gave one string
        if isinstance(self.stop, str):
            self.stop = [self.stop]

        # if remote provider, ensure some API key reference exists
        if self.inferred_provider not in {"local", "other"}:
            key_in_extra = "api_key" in self.extra
            if not (self.api_key_env or key_in_extra):
                raise ValueError(
                    f"{self.inferred_provider}: provide api_key_env or extra['api_key']"
                )

        return self

    # ­­­­­­­­­­­ helper props ­­­­­­­­­­­
    @property
    def inferred_provider(self) -> str:
        if self.provider:
            return self.provider
        if "/" in self.name:
            return self.name.split("/", 1)[0]
        raise ValueError("You should define your LLM provider, either in its name e.g openai/gpt-4o-mini or explicitly in yaml.")
    
    @property
    def inferred_model(self) -> str:
        if self.name:
            if "/" in self.name:
                return self.name.split("/", 1)[-1]
            
        raise ValueError("You should set the model name. e.g. 'gpt-4o-mini', 'anthropic/claude-3-sonnet'")

    # ­­­­­­­­­­­ factory ­­­­­­­­­­­
    def build(self) -> "dspy.LM":

        kwargs: Dict[str, Any] = dict(
            model=self.name,
            model_type=self.model_type,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=self.stop,
            cache=self.cache,
            num_retries=self.num_retries,
            provider=self.provider or self.inferred_provider,
            api_base=self.api_base_url,
            finetuning_model=self.finetuning_model,
            **self.extra,
        )

        # resolve API key from env at runtime (if set)
        if self.api_key_env and "api_key" not in kwargs:
            api_key_val = os.getenv(self.api_key_env)
            if api_key_val:
                kwargs["api_key"] = api_key_val

        # strip None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return dspy.LM(**kwargs)
