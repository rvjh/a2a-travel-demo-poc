import os
from typing import Type, TypeVar

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel

load_dotenv()

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self):
        
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")

        self.client = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=0.1,
        )

    def structured_complete(self, system: str, user: str, response_model: Type[T]) -> T:

        structured_llm = self.client.with_structured_output(response_model)
        response = structured_llm.invoke(
            [
                ("system", system),
                ("human", user)
            ])
            
        return response
