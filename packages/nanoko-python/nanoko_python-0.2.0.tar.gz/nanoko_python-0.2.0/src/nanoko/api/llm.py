from typing import Optional, List
from httpx import Client, AsyncClient

from nanoko.models.llm import LLMMessage
from nanoko.exceptions import raise_nanoko_api_exception


class LLMAPI:
    """The API for the LLM."""

    def __init__(self, base_url: str = "http://localhost:25324", client: Client = None):
        self.base_url = base_url
        self.client = client or Client()

    def get_hint(
        self,
        sub_question_id: int,
        question: str,
        context: Optional[List[LLMMessage]] = None,
    ) -> str:
        """Get a hint for the sub-question.

        Args:
            sub_question_id (int): The ID of the sub-question.
            question (str): The question to ask.
            context (Optional[List[LLMMessage]]): The context to send to the LLM.

        Returns:
            str: The hint for the sub-question.
        """
        params = {
            "sub_question_id": sub_question_id,
            "question": question,
            "context": [],
        }
        if context:
            params["context"] = [message.model_dump() for message in context]
        response = self.client.post(f"{self.base_url}/api/v1/llm/hint", json=params)
        raise_nanoko_api_exception(response)
        return response.json()["hint"]


class AsyncLLMAPI:
    """The async API for the LLM."""

    def __init__(
        self, base_url: str = "http://localhost:25324", client: AsyncClient = None
    ):
        self.base_url = base_url
        self.client = client or AsyncClient()

    async def get_hint(
        self,
        sub_question_id: int,
        question: str,
        context: Optional[List[LLMMessage]] = None,
    ) -> str:
        """Get a hint for the sub-question.

        Args:
            sub_question_id (int): The ID of the sub-question.
            question (str): The question to ask.
            context (Optional[List[LLMMessage]]): The context to send to the LLM.

        Returns:
            str: The hint for the sub-question.
        """
        params = {
            "sub_question_id": sub_question_id,
            "question": question,
        }
        if context:
            params["context"] = [message.model_dump() for message in context]
        response = await self.client.post(
            f"{self.base_url}/api/v1/llm/hint", json=params
        )
        raise_nanoko_api_exception(response)
        return response.json()["hint"]
