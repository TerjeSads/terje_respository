# Copilot Project Instructions

Concise guidance for AI coding agents working in this repository. Focus on these project-specific conventions and workflows before making changes.

## 1. Purpose & Architecture
- Minimal Streamlit template for internal ADS apps.
- Entry point: `st_app.py` configures page + builds navigation via `st.navigation([st.Page(...)])` pointing to scripts under `gui_pages/`.
- Pages (`gui_pages/page1.py`, `page2.py`) are simple Streamlit scripts. Page1 demonstrates data access patterns.
- Shared infra code lives in `common/`:
  - `connectivity.py`: creates global clients (SQLAlchemy engine, BigQuery client, GCS client) at import time with fallback to in-memory SQLite if SQL Server connection fails.
  - `data_queries.py`: example parameterized query functions for SQL Server & BigQuery; imports shared clients.
- Data flow: UI (Streamlit page) -> call query helper (returns DataFrame) -> display via `st.dataframe`.
- External service boundaries: SQL Server (via `telenor-sads-connectivity` engines), BigQuery & GCS (Google Cloud clients), internal SADS APIs (`sadsapi`).

## 2. Runtime & Tooling
- Python version pinned: `>=3.13` (pyproject). Use `uv` to manage env + dependencies.
- Install deps: `uv sync` (creates `.venv`). Run commands through `uv run <cmd>`.
- Streamlit launch: `uv run streamlit run st_app.py`.
- Lint / format: `uv run ruff check .` and `uv run ruff format .`.
- Dev extras (ipykernel, pre-commit): `uv sync --group dev`.
- Upgrade deps: `uv lock --upgrade` then `uv sync` (ensure app still runs).

## 3. Dependency Management
- All dependencies declared in `pyproject.toml`; resolved versions in `uv.lock` (commit both on changes).
- Internal packages sourced from custom index `[tool.uv.index]` using OAuth token placeholder (`oauth2accesstoken@`). Do NOT hardcode credentials; rely on `gcloud auth login` + `gcloud auth application-default login` for ADC.
- Add a package: `uv add <name>`; Remove: edit `pyproject.toml` then `uv sync`.

## 4. Patterns & Conventions
- Centralized clients: Do NOT recreate BigQuery / SQL engines inside every function; import from `common.connectivity`.
- Parameterized SQL only: use SQLAlchemy `text()` plus named parameters (see `example_sql_function`). Avoid string interpolation in queries.
- Error handling pattern: wrap data-access in try/except and surface issues via `st.error` returning empty `pd.DataFrame()` to keep UI responsive.
- Pages should remain lean: UI composition + calling helper functions only.
- New shared logic goes in `common/` (create new module if needed) rather than embedding large logic in page scripts.
- Keep imports explicit; avoid wildcard imports.
- Navigation: update the list in `st_app.py` when adding a page; file path given as string to `st.Page()`.

## 5. Adding a New Feature (Example Flow)
1. Create `gui_pages/my_feature.py` with Streamlit UI.
2. If data access needed: add function in `common/<new_module>.py` reusing shared clients.
3. Import new function(s) in the page; handle errors as per existing pattern.
4. Register page in `st_app.py` navigation list.
5. Run: `uv run streamlit run st_app.py` and verify page loads.
6. Lint & format before commit.

## 6. Deployment Considerations
- Cloud Run detection via `K_SERVICE` toggles IAM PSC SQL engine path. Ensure new code does not break this import-time logic.
- Avoid side effects at import except for lightweight client creation (current pattern). Expensive operations should move inside functions.
- Do not introduce blocking calls at top-level in pages; Streamlit reruns script on interaction.

## 7. Testing Guidance (Future Expansion)
- Currently no tests. If adding: prefer lightweight functional tests for data helpers using mocked engines/clients; avoid hitting real external services.
- Place tests under `tests/` (create directory) and run via `uv run pytest` once Pytest added to dev deps.

## 8. Common Pitfalls
- Forgetting to authenticate to Google Cloud -> BigQuery queries fail; instruct user to run `gcloud auth application-default login`.
- Creating duplicate DB engines -> resource leakage; reuse `sql_engine`.
- Hardcoding credentials -> reject; rely on ADC.
- Modifying Python requirement without checking dependent package compatibility.

## 9. Safe Change Checklist (Pre-PR)
- App launches locally without stack traces.
- Navigation still works; all listed pages import successfully.
- `uv run ruff check .` passes (or explicitly justify ignored issues).
- No new top-level network calls other than client initialization.
- Updated README if user-facing workflow changes.

## 10. Quick Reference Commands
```bash
uv sync                     # install deps
uv run streamlit run st_app.py  # run app
uv run ruff check .         # lint
uv run ruff format .        # format
uv lock --upgrade && uv sync # upgrade deps
```

---
If any of the above seems ambiguous, open an issue or extend this file with clarifications discovered during implementation.
