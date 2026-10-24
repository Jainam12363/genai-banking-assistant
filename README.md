# GenAI Banking Assistant

A conversational banking assistant built with Python, LangGraph,
LangChain, FastAPI, Streamlit, MCP, and SQLite.

> **Important:** This is a demonstration project using mock banking
> data. It is not connected to a real bank and must not be used for real
> financial transactions or production banking.

## Overview

The assistant answers natural-language questions about mock banking
data, researches information from approved official financial sources,
and supports predefined banking operations that require explicit
confirmation in the UI.

## Features

-   Natural-language banking questions about accounts, transactions,
    customers, support tickets, and supported calculations.
-   LangGraph workflow routing between a Banking Agent and a Web
    Research Agent.
-   MCP-backed tools for banking operations and official-source
    research.
-   FastAPI backend and SQLite mock banking database.
-   Streamlit chat interface.
-   Voice input using Groq Whisper transcription, with transcription
    review/edit before submission.
-   Streaming responses.
-   Persistent conversation history using LangGraph checkpointing and
    conversation metadata.
-   Hybrid sensitive-data detection using Microsoft Presidio, spaCy,
    regular expressions, contextual detection, and custom recognizers.
-   Official-source web research restricted to configured domains,
    including RBI, NPCI, SEBI, IRDAI, PFRDA, and the Income Tax
    Department.
-   Human confirmation before supported database mutations.

## Supported banking operations

1.  Freeze an eligible account.
2.  Unfreeze an eligible frozen account.
3.  Update a customer's phone number.
4.  Update a customer's email address.
5.  Block an eligible card.
6.  Unblock an eligible blocked card.
7.  Create a support ticket.
8.  Update permitted support-ticket fields.

For state-changing operations, LangGraph intercepts the proposed action
and the Streamlit UI asks the user to confirm or cancel. On
confirmation, the action goes through an MCP tool, FastAPI endpoint, and
validated database service. The implementation uses predefined
operations rather than model-generated arbitrary SQL.

## Architecture

``` text
User
 |
 v
Streamlit UI <----> FastAPI
                      |
                      v
                LangGraph workflow
                  /          \
                 v            v
          Banking Agent   Web Research Agent
                 \            /
                  v          v
                    MCP tools
                       |
              +--------+--------+
              |                 |
              v                 v
        Banking API/data   Official-source
              |             research
              v
        SQLite mock DB
```

Privacy processing is applied in the agent workflow. State-changing
actions require explicit UI confirmation.

## Technology stack

  Technology           Purpose
  -------------------- -----------------------------------------
  Python               Main language
  LangChain            LLM and tool integration
  LangGraph            Workflow orchestration and state
  Groq                 LLM inference and speech transcription
  FastAPI              Backend API
  Streamlit            Frontend
  MCP                  Standardized tool integration
  SQLite               Mock banking data and local persistence
  Microsoft Presidio   Sensitive-data analysis
  spaCy                NLP support for entity detection
  Requests             HTTP communication

## Project structure

The exact contents can vary by checkout. Main components include:

``` text
V2/
├── agents/
│   ├── banking_agent.py
│   ├── web_research_agent.py
│   └── prompts.py
├── api/
│   ├── main.py
│   └── database_service.py
├── graph/
│   ├── agent_graph.py
│   ├── nodes.py
│   └── state.py
├── mcp_integration/
│   ├── server.py
│   └── langchain_tools.py
├── privacy/
├── services/
├── streamlit_app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites

-   Windows 10/11 or another supported OS.
-   A compatible Python version.
-   Git.
-   A Groq API key for the configured LLM and transcription features.
-   Internet access for model calls and official-source research.

Check versions:

``` powershell
python --version
git --version
```

## Setup on Windows

### 1. Clone the repository

``` powershell
git clone https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME
```

Replace the placeholders with the real repository details.

### 2. Create and activate a virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Use the versions in your known-working requirements file. Avoid
upgrading all LangChain, LangGraph, and MCP packages indiscriminately.

### 4. Configure environment variables

Create a local `.env` file in the project root. Do not commit it. The
project uses `GROQ_API_KEY`; inspect `config.py` for the complete set of
variables and defaults.

Example only:

``` dotenv
GROQ_API_KEY=replace_with_your_own_key
LLM_MODEL=replace_with_your_configured_model
```

Keep placeholders only in `.env.example`.

### 5. Prepare the mock database

The project has used a local `banking.db`. It may not be present after
cloning because runtime databases should not normally be committed. Use
an approved local mock database or add a seed/initialization script.
Confirm the path and initialization logic in the code; do not assume
automatic database creation unless implemented.

## Running the application

Open a terminal at the project root, activate the virtual environment,
and start FastAPI:

``` powershell
uvicorn api.main:app --reload
```

Open a second terminal and start Streamlit:

``` powershell
streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit. Confirm the API URL and port in
the project's configuration if the defaults differ.

Follow the MCP startup lifecycle in `mcp_integration/server.py` and
`mcp_integration/langchain_tools.py`. The MCP server may be started by
the client as a subprocess, or may require separate startup depending on
the current configuration.

## Example questions

Banking data:

``` text
What is the balance of account 8385972235?
Show the recent transactions for account 8385972235.
Show the support tickets for customer 3.
```

Official-source research:

``` text
What is the latest RBI monetary policy update?
What are the current UPI transaction limits according to NPCI?
Find recent official SEBI regulatory updates.
```

Supported operations:

``` text
Freeze my account 8385972235.
Unfreeze my account 8385972235.
Update my phone number to 9876543210.
Update my email address to test.customer@example.com.
Block card 1.
Unblock card 1.
Create a high priority support ticket for customer 3 regarding a failed payment from account 8385972235. The payment failed while making a transaction.
Update support ticket 102 and change its priority to HIGH and status to IN_PROGRESS.
```

These operation examples depend on the local database records and their
current statuses. For repeatable demos, reset or seed a known demo
database before presenting.

## Privacy and limitations

The privacy layer combines configured patterns and NLP-based detection
to identify values such as email addresses, phone numbers, person names,
locations, IP addresses, card numbers, account numbers, PAN values, and
customer IDs. Detection can produce false positives and false negatives;
it is not a guarantee that every sensitive value will be found.

Anonymization does not replace authentication, authorization,
encryption, or secure logging. Do not use real customer data without
appropriate authorization and safeguards.

## Database and persistence

The mock banking database stores customers, accounts, transactions,
cards, loans, beneficiaries, tickets, and branches. Separate local
persistence is used for conversation metadata and LangGraph checkpoints.

Do not commit mutable databases, checkpoint files, or personal data. For
reproducibility, provide safe seed data or documented initialization
steps.

## Troubleshooting

-   **Missing `GROQ_API_KEY`:** Check the local `.env`, variable
    spelling, and environment-loading code. Restart the backend after
    changes.
-   **Streamlit cannot reach FastAPI:** Ensure the API is running and
    the configured URL and port match.
-   **Missing database/table:** Verify the configured path and
    initialize or restore a safe mock database.
-   **MCP tool failure:** Check server/client configuration, API
    reachability, and logs. Keep debug output off STDOUT when using MCP
    STDIO transport.
-   **Voice transcription failure:** Check the API key, network, audio
    format, and installed dependencies.
-   **Action does not run:** Check that the record exists and is in an
    allowed state, then verify the actual database record. A UI success
    message alone is not database verification.

## Security notes

-   This is a mock-data demo, not a production banking system.
-   Never commit `.env`, keys, passwords, tokens, or connection strings.
-   Exclude `.venv`, Python caches, logs, local databases, checkpoint
    files, and temporary backups from Git.
-   Keep database mutations limited to predefined validated operations.
-   UI confirmation is a safeguard, not a complete authorization system.
-   Production use would require authentication, authorization, audit
    logging, secure secret management, and security testing.

## Future improvements

-   Reproducible demo database seed/reset script.
-   Automated tests for the eight controlled actions.
-   Audit logs for confirmed and cancelled operations.
-   More robust health checks, error handling, and test coverage.

## Disclaimer

This project is intended for learning, prototyping, and demonstration.
It uses mock banking data and should not be used to perform real
financial operations or make decisions about real customers.
