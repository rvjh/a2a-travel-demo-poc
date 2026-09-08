Absolutely — here is a fuller `README.md` that keeps the important explanations from your original version but removes unnecessary repetition and aligns it with the **actual Router, Flight, Hotel, A2A, and MCP architecture**.

 Agent Cards README

# Agent Cards

## Overview

 **Agent Cards** are used for **A2A (Agent-to-Agent) agent discovery**.

 An Agent Card provides basic information about an agent, including:

- Agent name
- Agent description
- Agent endpoint
- Supported skills/capabilities

 The standard discovery endpoint is:

```
GET /.well-known/agent-card.json
```

 Another agent or client can call this endpoint to discover what an agent does and where it can be reached.

---

# Agent Architecture

 The travel system contains three agents:

```
                         USER
                           |
                           v
                +----------------------+
                |  Travel Router Agent |
                +----------+-----------+
                           |
                    Agent-to-Agent
                       HTTP calls
                     /           \
                    v             v
           +-------------+   +-------------+
           | Flight Agent|   | Hotel Agent |
           +------+------+   +------+------+
                  |                 |
                 MCP               MCP
                  |                 |
                  v                 v
           Flight Tools       Hotel Tools
```

 The responsibilities are:

| Agent               | Responsibility                           |
| ------------------- | ---------------------------------------- |
| Travel Router Agent | Orchestrates the travel planning process |
| Flight Agent        | Searches and recommends flights          |
| Hotel Agent         | Searches and recommends hotels           |

---

# Agent Card Endpoints

 The Flight and Hotel Agents currently expose Agent Cards.

## Flight Agent

```
GET http://127.0.0.1:8001/.well-known/agent-card.json
```

 Agent endpoint:

```
http://127.0.0.1:8001
```

## Hotel Agent

```
GET http://127.0.0.1:8002/.well-known/agent-card.json
```

 Agent endpoint:

```
http://127.0.0.1:8002
```

## Travel Router Agent

 The Router Agent runs on:

```
http://127.0.0.1:8000
```

 The current Router implementation does **not** expose:

```
/.well-known/agent-card.json
```

 Instead, it acts as the main orchestrator and communicates with the Flight and Hotel Agents.

---

# Flight Agent Card

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

| Field           | Value                                     | Purpose                |
| --------------- | ----------------------------------------- | ---------------------- |
| `name`        | `flight-agent`                          | Identifies the agent   |
| `description` | `Finds flights for travel destinations` | Describes the agent    |
| `url`         | `http://127.0.0.1:8001`                 | Agent endpoint         |
| `skills`      | `flight_search`, `flight_price`       | Supported capabilities |

 The Flight Agent is responsible for flight-related operations.

 Its general flow is:

```
Flight Request
      |
      v
Flight Agent
      |
      v
MCP Gateway
      |
      v
search_flights
      |
      v
Flight Data
      |
      v
LLM Recommendation
      |
      v
FlightAgentResult
```

---

# Hotel Agent Card

 Calling:

```
GET http://127.0.0.1:8002/.well-known/agent-card.json
```

 returns:

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

| Field           | Value                                    | Purpose                |
| --------------- | ---------------------------------------- | ---------------------- |
| `name`        | `hotel-agent`                          | Identifies the agent   |
| `description` | `Finds hotels for travel destinations` | Describes the agent    |
| `url`         | `http://127.0.0.1:8002`                | Agent endpoint         |
| `skills`      | `hotel_search`, `hotel_price`        | Supported capabilities |

 The Hotel Agent is responsible for hotel-related operations.

 Its general flow is:

```
Hotel Request
      |
      v
Hotel Agent
      |
      v
MCP Gateway
      |
      v
search_hotels
      |
      v
Hotel Data
      |
      v
LLM Recommendation
      |
      v
HotelAgentResult
```

---

# Why Agent Cards Are Important

 Agent Cards allow agents to discover other agents without needing to know their implementation details.

 An agent can learn:

```
Who are you?
      |
      v
What do you do?
      |
      v
Where can I call you?
      |
      v
What skills do you provide?
```

 For example, the Flight Agent Card tells the system:

```
Name:
flight-agent

Endpoint:
http://127.0.0.1:8001

Skills:
- flight_search
- flight_price
```

 The client now knows that the Flight Agent is responsible for flight-related requests.

---

# Agent Card Structure

 A basic Agent Card contains:

```
Agent Card
    |
    +-- name
    |
    +-- description
    |
    +-- url
    |
    +-- skills
```

 For example:

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

---

# Agent Card vs MCP

 Agent Cards and MCP have different responsibilities.

## Agent Card

 Agent Cards are mainly used for **agent discovery**.

 They describe:

```
Agent Card
    |
    +-- Identity
    +-- Description
    +-- Endpoint
    +-- Skills
```

 They answer:

> **"Who are you and what can you do?"**

---

## MCP

 MCP is used for **tool discovery and tool execution**.

 It provides:

```
MCP
 |
 +-- Tools
 +-- Tool schemas
 +-- Tool inputs
 +-- Tool execution
 +-- Tool results
```

 It answers:

> **"What tools can you use and how can they be executed?"**

---

# Comparison

| Feature               | Agent Card      | MCP                      |
| --------------------- | --------------- | ------------------------ |
| Purpose               | Agent discovery | Tool discovery/execution |
| Identifies agent      | Yes             | No                       |
| Provides agent URL    | Yes             | No                       |
| Describes skills      | Yes             | Describes tools          |
| Provides tool schemas | No              | Yes                      |
| Executes tools        | No              | Yes                      |
| Returns tool results  | No              | Yes                      |
| Main question         | "Who are you?"  | "What can I execute?"    |

---

# A2A Communication

 The Travel Router communicates with the Flight and Hotel Agents using HTTP.

 For example:

```
Travel Router
      |
      | HTTP POST
      v
Flight Agent
```

 and:

```
Travel Router
      |
      | HTTP POST
      v
Hotel Agent
```

 The Router sends the user's request to the required specialized agent.

 Example:

```
{
  "message": "Plan a 3 day trip to Goa. Find a flight and hotel."
}
```

 The Flight Agent receives the request and returns a `FlightAgentResult`.

 The Hotel Agent receives the request and returns a `HotelAgentResult`.

---

# Complete System Flow

 For a request such as:

```
Plan a 3 day trip to Goa.
Find me a flight and hotel.
```

 the system works like this:

```
                         USER
                           |
                           v
                Travel Router Agent
                           |
                           v
                     Router LLM
                           |
                           v
                   Router Decision
                           |
              +------------+------------+
              |                         |
              v                         v
        Flight Agent              Hotel Agent
              |                         |
              v                         v
        MCP Gateway              MCP Gateway
              |                         |
              v                         v
       search_flights             search_hotels
              |                         |
              v                         v
       Flight Results            Hotel Results
              |                         |
              +------------+------------+
                           |
                           v
                    Travel Router
                           |
                           v
                     Travel Plan
                           |
                           v
                          USER
```

---

# Example Discovery Flow

 Before communicating with an agent, a client can discover its Agent Card.

 For the Flight Agent:

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

 The client receives:

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

 The client now knows that the Flight Agent can handle flight-related tasks.

---

# Agent Card and MCP Together

 The Flight Agent demonstrates how Agent Cards and MCP work together.

 First, the Agent Card provides **agent discovery**:

```
Client
   |
   | Agent Card
   v
Flight Agent
```

 Then the Flight Agent uses MCP for **tool access**:

```
Flight Agent
      |
      | MCP
      v
MCP Gateway
      |
      v
search_flights
      |
      v
Flight Data
```

 The same pattern applies to the Hotel Agent:

```
Client
   |
   | Agent Card
   v
Hotel Agent
   |
   | MCP
   v
MCP Gateway
   |
   v
search_hotels
```

---

# Three Layers of the System

 The overall architecture can be understood as three separate layers.

## 1\. Agent Discovery

 Agent Cards answer:

```
Who is this agent?
Where is it?
What skills does it have?
```

```
Agent Card
    |
    +-- Identity
    +-- URL
    +-- Skills
```

## 2\. Agent-to-Agent Communication

 The Router communicates with specialized agents:

```
Travel Router
      |
      +---- HTTP ----> Flight Agent
      |
      +---- HTTP ----> Hotel Agent
```

## 3\. Tool Execution

 Specialized agents use MCP:

```
Flight Agent
      |
      +---- MCP ----> search_flights

Hotel Agent
      |
      +---- MCP ----> search_hotels
```

---

# Final Architecture

```
                              USER
                                |
                                | HTTP
                                v
                    +-------------------------+
                    |   Travel Router Agent   |
                    |        :8000            |
                    +------------+------------+
                                 |
                       Agent-to-Agent HTTP
                         /               \
                        /                 \
                       v                   v
             +----------------+   +----------------+
             |  Flight Agent  |   |   Hotel Agent  |
             |     :8001      |   |      :8002     |
             +-------+--------+   +-------+--------+
                     |                    |
                    MCP                  MCP
                     |                    |
                     v                    v
             +---------------+    +---------------+
             | MCP Gateway   |    | MCP Gateway   |
             +-------+-------+    +-------+-------+
                     |                    |
                     v                    v
              search_flights        search_hotels
```

 Agent Cards describe the agents:

```
Flight Agent
    ↓
flight_search
flight_price

Hotel Agent
    ↓
hotel_search
hotel_price
```

 MCP provides the actual tools:

```
search_flights
search_hotels
```

---

# Key Takeaways

- **Agent Card = Agent discovery**
- **A2A = Agent-to-agent communication**
- **MCP = Tool discovery and execution**
- **Flight Agent = Flight specialist**
- **Hotel Agent = Hotel specialist**
- **Travel Router = Main orchestrator**
- `/.well-known/agent-card.json` is the discovery endpoint.
- Agent Cards describe **agents and their capabilities**.
- MCP describes and executes **tools**.

 In simple terms:

```
Agent Card
    ↓
"Who are you?"
"What can you do?"
"Where can I call you?"

A2A
    ↓
"Let me communicate with another agent."

MCP
    ↓
"Let me use a tool."
```
