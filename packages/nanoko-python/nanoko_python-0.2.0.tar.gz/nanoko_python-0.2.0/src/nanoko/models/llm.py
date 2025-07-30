from typing import Literal
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """LLM message model for LLM"""

    role: Literal["user", "assistant"]
    content: str
