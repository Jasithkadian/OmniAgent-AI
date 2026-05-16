# Veyra Project Instructions

This project is an AI-powered orchestration platform. Use the following guidelines when working in this codebase.

## Sandbox Environment

We have configured a custom sandbox for the Gemini CLI to ensure all tool executions (testing, linting, etc.) happen in a controlled environment with the correct dependencies.

### How to use the Sandbox

To run Gemini CLI with the custom sandbox:

1.  **Enable Docker Sandbox**:
    ```bash
    export GEMINI_SANDBOX=docker
    ```
2.  **Build the Sandbox Image** (first time or when Dockerfile changes):
    ```bash
    BUILD_SANDBOX=1 gemini
    ```
3.  **Run with Sandbox**:
    ```bash
    gemini -s "run the backend tests"
    ```

The sandbox is defined in `.gemini/sandbox.Dockerfile` and includes:
- Python 3.11
- Backend dependencies (from `backend/requirements.txt`)
- Node.js & NPM
- Development tools: `pytest`, `ruff`, `black`, `mypy`

## Development Workflows

- **Backend**: FastAPI app located in `backend/app`.
- **Agents**: Core agent logic in `agents/`.
- **RAG**: Retrieval-Augmented Generation pipeline in `rag/`.
- **Testing**: Run tests using `pytest`.

## Architectural Principles

- **Surgical Changes**: Always prioritize targeted updates over broad refactors.
- **Type Safety**: Use Pydantic schemas for data validation and SQLAlchemy for database interactions.
- **Traceability**: Ensure agent actions and blackboard updates are logged.
