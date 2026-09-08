14. Agent Cards
Now every A2A agent exposes:

GET /.well-known/agent-card.json

Flight:

http://127.0.0.1:8001/.well-known/agent-card.json

Hotel:

http://127.0.0.1:8002/.well-known/agent-card.json

For example:

{
  "name": "flight-agent",
  "description": "Finds flights for travel destinations",
  "url": "http://127.0.0.1:8001",
  "skills": [
    "flight_search",
    "flight_price"
  ]
}

The important conceptual difference is:

Agent Card
    |
    +--> identity
    +--> URL
    +--> capabilities
    +--> skills

while MCP exposes:

MCP
 |
 +--> tools
 +--> tool schemas
 +--> tool execution