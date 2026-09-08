# Agent Cards

 Agent Cards allow A2A (Agent-to-Agent) agents to **advertise their identity, endpoint, capabilities, and supported skills**.

 Each A2A agent exposes a standard discovery endpoint:

```
GET /.well-known/agent-card.json
```

 A client or another agent can call this endpoint to discover what an agent is and what it can do.

---

## Agent Card Endpoints

 Currently, the system has two A2A agents.

### Flight Agent

```
http://127.0.0.1:8001/.well-known/agent-card.json
```

 The Flight Agent provides flight-related capabilities.

### Hotel Agent

```
http://127.0.0.1:8002/.well-known/agent-card.json
```

 The Hotel Agent provides hotel-related capabilities.

---

## Flight Agent Card

 Calling:

```
GET http://127.0.0.1:8001/.well-known/agent-card.json
```

 returns:

```
{
  "name": "flight-agent",
  "description": "Finds flights for travel destinations",
  "url": "http://127.0.0.1:8001",
  "skills": [
    "flight_search",
    "flight_price"
  ]
}
```

### Flight Agent Information

| Field           | Value                                     | Purpose                            |
| --------------- | ----------------------------------------- | ---------------------------------- |
| `name`        | `flight-agent`                          | Unique agent name                  |
| `description` | `Finds flights for travel destinations` | Describes the agent                |
| `url`         | `http://127.0.0.1:8001`                 | Agent endpoint                     |
| `skills`      | `flight_search`, `flight_price`       | Capabilities provided by the agent |

---

## Hotel Agent Card

 Calling:

```
GET http://127.0.0.1:8002/.well-known/agent-card.json
```

 returns information about the Hotel Agent.

 Example:

```
{
  "name": "hotel-agent",
  "description": "Finds hotels for travel destinations",
  "url": "http://127.0.0.1:8002",
  "skills": [
    "hotel_search",
    "hotel_price"
  ]
}
```

### Hotel Agent Information

| Field           | Value                                    | Purpose                            |
| --------------- | ---------------------------------------- | ---------------------------------- |
| `name`        | `hotel-agent`                          | Unique agent name                  |
| `description` | `Finds hotels for travel destinations` | Describes the agent                |
| `url`         | `http://127.0.0.1:8002`                | Agent endpoint                     |
| `skills`      | `hotel_search`, `hotel_price`        | Capabilities provided by the agent |

---

# Why Agent Cards Are Important

 An Agent Card provides **metadata about an agent**.

 It allows another agent or client to answer questions such as:

- Who is this agent?
- What does this agent do?
- Where can I send requests?
- What skills does this agent provide?

 Conceptually:

```
                    Agent Card
                        |
        +---------------+---------------+
        |               |               |
        v               v               v
     Identity          URL         Capabilities
                                        |
                                        v
                                      Skills
```

 For example:

```
Agent Card
    |
    +--> Name: flight-agent
    |
    +--> URL: http://127.0.0.1:8001
    |
    +--> Skills:
          |
          +--> flight_search
          +--> flight_price
```

---

# Agent Card vs MCP

 Agent Cards and MCP serve **different purposes**.

## Agent Card

 An Agent Card is primarily used for **agent discovery and metadata**.

 It describes:

```
Agent Card
    |
    +--> Identity
    +--> URL
    +--> Description
    +--> Capabilities
    +--> Skills
```

 It answers:

> **"Who are you and what can you do?"**

---

## MCP

 MCP is used for **tool discovery and tool execution**.

 It exposes:

```
MCP
 |
 +--> Tools
 +--> Tool Schemas
 +--> Tool Inputs
 +--> Tool Execution
 +--> Tool Results
```

 It answers:

> **"What tools can I call, how do I call them, and what result do they return?"**

---

# Conceptual Difference

 The distinction can be visualized as:

```
                 A2A Agent
                    |
          +---------+---------+
          |                   |
          v                   v
     Agent Card              MCP
          |                   |
          |                   |
          v                   v
      Discovery           Tool Access
          |                   |
          +                   +
          |                   |
      Who are you?       What can I execute?
          |                   |
          v                   v
      Identity             Tools
      URL                  Schemas
      Skills               Execution
      Capabilities         Results
```

---

# Agent Card vs MCP Comparison

| Feature               | Agent Card      | MCP                          |
| --------------------- | --------------- | ---------------------------- |
| Purpose               | Agent discovery | Tool discovery and execution |
| Identifies agent      | Yes             | No                           |
| Provides agent URL    | Yes             | Not its primary purpose      |
| Describes skills      | Yes             | Describes tools              |
| Exposes tools         | No              | Yes                          |
| Provides tool schemas | No              | Yes                          |
| Executes tools        | No              | Yes                          |
| Answers               | "Who are you?"  | "What can I execute?"        |

---

# Example End-to-End Flow

 Suppose a system wants to find a flight.

 First, it can discover the Flight Agent:

```
Client
  |
  | GET /.well-known/agent-card.json
  v
Flight Agent
  |
  | Agent Card
  v
Client
```

 The client learns:

```
Name: flight-agent

Skills:
- flight_search
- flight_price

URL:
http://127.0.0.1:8001
```

 The client now knows that the Flight Agent can handle flight-related requests.

 Separately, the Flight Agent uses MCP to access its flight search tool:

```
Flight Agent
     |
     | MCP
     v
MCP Gateway
     |
     | search_flights
     v
Flight Search Tool
     |
     v
Flight Results
```

 Therefore:

```
Agent Card
     |
     | Discover the agent
     v
Flight Agent
     |
     | Use tools
     v
MCP
     |
     v
Flight Data
```

---

# Key Takeaway

 **Agent Cards describe the agent, while MCP provides access to tools.**

```
Agent Card
    |
    +--> Identity
    +--> URL
    +--> Capabilities
    +--> Skills

MCP
    |
    +--> Tools
    +--> Tool Schemas
    +--> Tool Execution
    +--> Tool Results
```

 In simple terms:

> **Agent Card = "Who are you and what can you do?"**

> **MCP = "What tools can you use and how can they be executed?"**
