Here’s a concise `README.md` that keeps the key architectural points without too much detail.

 Common Files README

# Common Files

 The `common` package contains the **shared models, configuration, and LLM setup** used across the travel agent system.

 The goal is to avoid duplicating definitions and to keep communication between services consistent.

```
common/
├── models.py
├── config.py
└── llm.py
```

---

## 1\. Pydantic Models — `common/models.py`

 This is an important part of the architecture.

 All shared request and response models are defined in one place using **Pydantic**.

 Instead of allowing every service to create its own JSON structure:

```
❌ Gateway → custom JSON
❌ Router  → different JSON
❌ Flight  → different JSON
❌ Hotel   → different JSON
```

 we use shared models:

```
common/models.py
        |
        +----------------+
        |                |
      Router           Flight
        |                |
      Hotel            Gateway
        |
       MCP
```

 This provides a **consistent data contract** between services.

 Examples of shared models include:

- `AgentRequest`
- `AgentCard`
- `Flight`
- `Hotel`
- `FlightAgentResult`
- `HotelAgentResult`
- `RouterDecision`
- `TravelPlan`

 Pydantic also validates the data exchanged between agents.

---

## 2\. Configuration — `common/config.py`

 `common/config.py` contains shared configuration used by the services.

 It keeps values such as:

- LLM configuration
- Flight Agent URL
- Hotel Agent URL
- MCP Gateway URL

 For example:

```
common/config.py
      |
      +── FLIGHT_AGENT_URL
      +── HOTEL_AGENT_URL
      +── MCP_GATEWAY_URL
      +── LLM configuration
```

 Keeping configuration in one place avoids hard-coding service URLs throughout the application.

---

## 3\. Shared LLM — `common/llm.py`

 `common/llm.py` contains the shared **LLM setup**.

 Agents can create the configured LLM using:

```
from common.llm import get_llm

llm = get_llm()
```

 The same LLM configuration can therefore be reused by:

```
Router Agent
     |
     +── get_llm()

Flight Agent
     |
     +── get_llm()

Hotel Agent
     |
     +── get_llm()
```

 The LLM also supports **structured output using Pydantic models**.

 For example:

```
llm.with_structured_output(RouterDecision)
```

 This allows the Router to receive a validated `RouterDecision` instead of relying on free-form JSON.

 The same approach can be used for the final `TravelPlan` or other structured agent responses.

---

# Why the `common` Package Matters

 The `common` package provides shared contracts and configuration for the entire system.

```
                  common/
                     |
        +------------+------------+
        |            |            |
     models.py    config.py     llm.py
        |            |            |
        v            v            v
   Data contracts  URLs/config  LLM setup
        |            |            |
        +------------+------------+
                     |
                     v
              All Agents/Services
```

### Key Takeaways

- **`models.py`** → Shared Pydantic data contracts
- **`config.py`** → Shared URLs and configuration
- **`llm.py`** → Shared LLM setup
- Pydantic keeps data formats **consistent and validated**
- Shared LLM configuration avoids duplicating LLM setup
- Structured LLM output works with the shared Pydantic schemas
