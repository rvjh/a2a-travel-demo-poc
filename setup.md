Here’s a clean **README setup-only** section based on your project structure and commands.

 README — Setup

# Setup

## 1\. Project Structure

```
a2a-travel-demo/
│
├── .env
├── requirements.txt
├── run_all.py
│
├── common/
│   ├── __init__.py
│   ├── config.py
│   ├── llm.py
│   └── models.py
│
├── mcp_gateway/
│   ├── __init__.py
│   └── main.py
│
├── agents/
│   ├── __init__.py
│   │
│   ├── flight_agent/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── hotel_agent/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   └── router_agent/
│       ├── __init__.py
│       └── main.py
│
├── gateway/
│   ├── __init__.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── test_mcp.py
│   ├── check_mcp_tools.py
│   └── test_agent.py
│
└── reports/
```

## 2\. Architecture

 The project is divided into the following components:

```
gateway/
    = External Travel API

agents/
    = A2A Agents

mcp_gateway/
    = Tool Gateway

common/
    = Contracts / Shared Infrastructure
```

## 3\. Create the Conda Environment

 From the project root directory, create the environment:

```
conda create --prefix ./venv python=3.14 -y
```

 Activate the environment:

```
conda activate ./venv
```

## 4\. Install Dependencies

 Install the required Python packages:

```
pip install -r requirements.txt
```

## 5\. Configure Environment Variables

 Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

 Replace `your_groq_api_key_here` with your actual Groq API key.

## 6\. Verify Setup

 After completing the setup, the project should have:

- The `venv` Conda environment created and activated.
- All dependencies installed from `requirements.txt`.
- A `.env` file containing the required Groq configuration.
- The project structure matching the structure shown above.
