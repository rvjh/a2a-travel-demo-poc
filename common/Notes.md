Common Pydantic models
This is important.

Don't let every service invent its own JSON format.

Everything shared goes into: common/models.py pydantic models are there

This gives you a consistent contract:

MCP
  ↓
Agent
  ↓
Pydantic
  ↓
A2A
  ↓
Pydantic
  ↓
Gateway


in llm_client.py

More specifically, it is doing three things:

Configuration: Loads GROQ_API_KEY and GROQ_MODEL from .env.
LLM initialization: Creates a ChatGroq instance.
LLM interaction: Provides structured_complete() as a reusable method for sending prompts and getting a structured Pydantic response.


