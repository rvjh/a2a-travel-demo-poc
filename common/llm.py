import os
from langchain_groq import ChatGroq
from common.config import GROQ_API_KEY

def get_llm():

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model="openai/gpt-oss-120b",
        temperature=0,
        max_tokens=1500,
        max_retries=3,
    )