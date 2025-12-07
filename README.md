E-Commerce Chatbot
===================

A lightweight, developer-focused chatbot that answers product and service questions for an e-commerce dataset using a combination of FAQ semantic search and SQL-backed retrieval.

Written from the perspective of a seasoned software engineer (20+ years): this README focuses on reproducible setup, clear operational guidance, and safe maintenance patterns.

Contents
--------
- Project summary
- Goals
- Architecture (text diagram)
- Component descriptions
- Quick start (PowerShell)
- Environment variables and secrets
- Dependencies
- Running (development and production notes)
- Database details and `db_path` guidance
- Resetting Chroma / embeddings
- Testing
- Troubleshooting
- Contribution guidelines
- Security considerations
- Appendix: .gitignore and .env example

Project summary
---------------
This repository implements an e-commerce-focused chatbot that can answer questions using two retrieval strategies:

- FAQ semantic search (vector database + embedding index)
- SQL-backed retrieval (natural language -> SQL -> SQLite query)

The project is intentionally lightweight so you can run it locally, iterate quickly, and extend the retrieval strategies to other vector stores or RDBMS systems.

Goals
-----
- Reproducible local development with minimal friction.
- Clear separation of concerns: routing, FAQ/embedding logic, and SQL-layer logic.
- Safe, documented procedures for resetting indexes and the local DB.
- Easy to containerize and deploy to production.

Architecture (ASCII diagram)
---------------------------
The following ASCII diagram shows the main request flow and persistence layers. This should help operators and contributors quickly understand how components interact.

Client (browser / test client)
   |
   |  HTTP / Streamlit calls
   v
+----------------+     +----------------+     +-----------------------------+
|  app/main.py   | --> |  app/router.py | --> | Handler: decides route      |
+----------------+     +----------------+     +-----------------------------+
                                                    /              \
                                                   /                \
                                                  v                  v
                                       +-------------------+   +------------------------+
                                       | faq.chain (faq.py) |   | sql.chain (sql.py)     |
                                       | - embedding lookup  |   | - LLM -> SQL generation |
                                       | - Chroma (vectors)  |   | - Executes read-only    |
                                       +-------------------+   |   queries against DB    |
                                                                 +------------------------+

Persistence (local dev defaults):
- Embeddings / vectors: Chroma (persistence dir, e.g., `./chroma_db`)
- Tabular product data: SQLite (authoritative file: `app/db.sqlite`)

Component descriptions
----------------------
- `app/main.py` — Streamlit entrypoint that manages the chat UI and session state.
- `app/router.py` — Simple routing logic that classifies queries and returns a route name (e.g., `faq` or `sql`).
- `app/faq.py` — Loads `resources/faq_data.csv`, creates/uses an embedding index (Chroma or analogous), and provides a `faq_chain` for retrieval.
- `app/sql.py` — Generates SQL (via an LLM or rules) and executes read-only queries against the local SQLite database. Uses a `db_path` configuration variable to locate the DB file (see Database details).
- `resources/` — CSV data: `ecommerce_data_final.csv` (product data) and `faq_data.csv` (FAQ data to seed the vector store).
- `app/db.sqlite` — Canonical SQLite file used for product queries in local development.

Quick start (PowerShell)
------------------------
1. Create a virtual environment and activate it:

   python -m venv .\.venv; .\.venv\Scripts\Activate.ps1

2. Install dependencies (ensure `requirements.txt` exists):

   pip install -r .\requirements.txt

3. Create or verify `.env` at repo root and set required variables (see "Environment variables" below).

4. Run the Streamlit app locally:

   .\.venv\Scripts\Activate.ps1; streamlit run app/main.py

Environment variables and secrets
---------------------------------
Use a `.env` file in development and a secret manager in production. Add `.env` to `.gitignore`.

Minimum variables (examples):
- `DB_PATH` — Optional. Absolute or relative path to the SQLite DB. Default: `./app/db.sqlite` (authoritative for this repo).
- `CHROMA_PERSIST_DIR` — Optional. Directory path used by Chroma for persistence (e.g., `./chroma_db`).
- `GROQ_MODEL` or `OPENAI_API_KEY` — If an LLM or external embedding provider is required, set the relevant keys.
- `LOG_LEVEL` — Optional. `INFO` or `DEBUG`.

Example `.env` content (values not included):

# .env (example)
DB_PATH=./app/db.sqlite
CHROMA_PERSIST_DIR=./chroma_db
GROQ_MODEL=your-model-here

Dependencies
------------
Ensure you have a `requirements.txt` or `pyproject.toml` with pinned versions. The implementation uses the following logical dependencies (adjust versions to your platform):

- python-dotenv
- pandas
- sqlite3 (builtin)
- streamlit
- chromadb (or configured vector store client)
- an embeddings provider client (OpenAI / sentence-transformers / vendor SDK)
- groq (if used for chat/completions in this project)

Running the app — development
-----------------------------
Use a development server with auto-reload for iterative work.

PowerShell dev command (example):

.\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Note: the repository contains a Streamlit-based entry (`app/main.py`). For Streamlit usage, start via `streamlit run app/main.py` as shown above in Quick start.

Running the app — production notes
---------------------------------
- Package the app into a container (Docker) and run behind a reverse proxy (nginx) and process manager.
- Use a managed or dedicated vector-store for production embedding persistence.
- Use an absolute `DB_PATH` and ensure proper file permissions for the SQLite file. Prefer a server-hosted RDBMS for heavy concurrency.

Database details and `db_path` guidance
--------------------------------------
This repository uses `app/db.sqlite` as the authoritative local database file. To avoid accidental duplication or confusion, the codebase should read the DB path from the environment with a clear default. Use the following pattern in `app/sql.py`:

  from pathlib import Path
  import os
  db_path = Path(os.getenv("DB_PATH", Path(__file__).parent / "db.sqlite"))

And always open the connection via:

  sqlite3.connect(str(db_path))

Test isolation:
- For unit or integration tests, use an in-memory DB (`:memory:`) or a temporary file to avoid clobbering `app/db.sqlite`.

Resetting Chroma / embeddings
-----------------------------
Two approaches to reset embeddings safely:
1) Remove the persistence directory (quick, destructive):

   Remove-Item -Recurse -Force .\chroma_db

   Then re-run the ingestion routine (e.g., `python app/faq.py` or the project's indexer script) to rebuild embeddings.

2) Programmatic reset (recommended for production):
- Provide a small maintenance script that calls the Chroma / vector-store admin API to delete collections safely, then re-seed.
- Example (pseudo-code):
  - client.delete_collection(name="faq")
  - run ingestion code

Important: back up the persistence directory before deleting in case you need to recover.

Testing
-------
Note: There are currently no test files in this repository.

Recommended next steps to add tests:
- Add unit tests for `app/sql.py` (parsing, validation, `run_query`) that use `:memory:` or temporary DB files.
- Add unit tests for `app/router.py` to verify routing decisions between `faq` and `sql`.
- Add integration tests that run the app endpoints via a lightweight test client (FastAPI TestClient or Streamlit test harness).

Sample commands to run tests (after adding tests):

.\.venv\Scripts\Activate.ps1; pytest -q

Troubleshooting
---------------
- Virtual environment not activated: ensure `.venv\Scripts\Activate.ps1` runs.
- Missing environment variables: verify `.env` and restart the process.
- Chroma permission errors: confirm the running user has read/write access to the persistence directory.
- SQLite locked: close other processes, or copy the DB and inspect. For automated tests, prefer `:memory:` DBs.

Contribution guidelines
-----------------------
- Fork the repository and create a topic branch: `feat/` or `fix/` prefix.
- Write tests for new functionality and keep changes small and focused.
- Follow code style: run `black` and check linting before opening a PR.
- Use descriptive commit messages and reference issue numbers in PR descriptions.

Security considerations
-----------------------
- Do not commit API keys or `.env` files. Add sensitive files to `.gitignore`.
- Sanitize user input before embedding or converting to SQL. Treat the SQL chain as an untrusted output — run LLM->SQL results through a validator that prevents destructive statements (e.g., only allow `SELECT` queries for retrieval).
- Rate-limit calls to external LLM services and monitor costs.

Sample CLI commands (PowerShell)
-------------------------------
# Create and activate virtual environment
python -m venv .\.venv; .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r .\requirements.txt

# Run Streamlit app
.\.venv\Scripts\Activate.ps1; streamlit run app/main.py

# Rebuild embeddings (destructive):
.\.venv\Scripts\Activate.ps1; Remove-Item -Recurse -Force .\chroma_db; python .\app\faq.py

# Reset local DB (destructive):
Remove-Item -Force .\app\db.sqlite

Appendix: recommended .gitignore and .env example
-------------------------------------------------
.gitignore snippet:

.venv/
__pycache__/
*.pyc
*.sqlite
chroma_db/
.env

.env example (do NOT commit):

DB_PATH=./app/db.sqlite
CHROMA_PERSIST_DIR=./chroma_db
GROQ_MODEL=your-model-here

Final notes (operator guidance)
------------------------------
- Choose an authoritative DB path and make it configurable via `DB_PATH` to avoid accidental file duplication.
- Add a small maintenance script (e.g., `scripts/reset_chroma.py`) to centralize index reset logic and avoid manual filesystem deletions.
- For production use, externalize secrets to a secret manager and use an enterprise-grade vector store or managed provider.

If you want, I can:
- add a `requirements.txt` with pinned versions based on scanning the repo,
- add a `scripts/` folder with a `reset_chroma.py` and a small `reset_db.ps1` helper,
- or update `app/sql.py` so it reads `DB_PATH` from environment and falls back to `app/db.sqlite`.

Created-by: experienced software engineer (20+ years) — tailored to help operators and maintainers set up, operate, and extend the system with low friction.
