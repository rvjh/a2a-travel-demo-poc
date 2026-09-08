Common Pydantic models
This is important.

Don't let every service invent its own JSON format.

Everything shared goes into: common/models.py pydantic models are there

This gives you a consistent contract:

Gateway
   |
Router
   |
Flight
   |
Hotel
   |
MCP

Configuration

common/config.py

configuration about llms and urls

Shared LLM common/llm.py

llm setup