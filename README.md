# ADS Template Streamlit App

Starter template for building internal Analytics & Data Science (ADS) Streamlit apps that connect to:

* SQL Server (read access, IAM / PSC aware)
* Google BigQuery
* Google Cloud Storage (and you can easily add Firestore, Logging, etc.)
* Internal SADS APIs (`sadsapi`, `sads-api-paths`, `sads-api-schemas`)

The template shows a minimal multi‑page Streamlit app (`st_app.py` + `gui_pages/`) with ready‑made connectivity helpers in `common/` and opinionated tooling (Python 3.13, `uv`, Ruff, pre‑commit).

---
## 0. Create Your Own Repository From This Template

If you haven't cloned yet and want to start a new project based on this template, the fastest way is to let GitHub create a new repo for you.

### 0.1 Using the "Use this template" Button (GitHub Web UI)
1. Go to the template repository page in your browser.
2. Click the green "Use this template" dropdown.
3. Choose "Create a new repository".
4. Fill in:
  * Owner: Your user or organization.
  * Repository name: e.g. `my-ads-app`.
  * Description: Short summary of your app.
  * Visibility: Usually Private for internal work.
  * (Optional) Uncheck "Include all branches" (keep only `main`).
5. Click "Create repository" – GitHub generates your new repo in a few seconds.

Now you have your own copy without editing the original template.

### 0.2a (Optional) Connect to a Remote Development Server via VS Code Remote SSH
If you develop on a shared Linux dev box or cloud VM, connect first and then clone the repo **inside** that remote environment so dependencies/install happen remotely.

Prerequisites:
* VS Code Desktop installed locally
* Extension: "Remote - SSH" (`ms-vscode-remote.remote-ssh`) (install via Extensions sidebar)
* SSH access to the target host (public key configured or password auth allowed)

Steps:
1. Open VS Code locally.
2. Install (or confirm) the Remote - SSH extension.
3. Again `Ctrl+Shift+P` → `Remote-SSH: Connect to Host...` → pick the host you just added.
4. A new VS Code window opens (green remote indicator in the lower-left). The first connection may install a VS Code server component—let it finish.


Notes:
* All `uv` commands now run on the remote machine; local environment is unaffected.
* If `curl` is missing remotely, install it (Debian/Ubuntu: `sudo apt-get update && sudo apt-get install -y curl`).


### 0.2 Open the Newly Created Repo in VS Code (GUI – No Terminal Needed)
Option A (Clone via Welcome Screen):
1. Open VS Code.
2. If the Welcome page is not visible, click Help > Welcome (or use Command Palette and type "Welcome").
3. Click "Clone Git Repository".
4. Paste the HTTPS URL of your new repo (from the green Code button on GitHub) and press Enter.
5. Choose an empty local folder location.
6. When prompted "Open Cloned Repository?" click "Open".
7. If asked to "Trust the authors" click Trust (required for running extensions & tasks).

Option B (Command Palette):
1. Press Ctrl+Shift+P (Cmd+Shift+P on macOS).
2. Type: `Git: Clone` and press Enter.
3. Paste repo URL → Enter → pick folder → Open.

Option C (GitHub VS Code Extension Signed In):
1. Sign in (Accounts icon in Activity Bar → GitHub Sign In) if not already.
2. Use the Source Control view → "Clone Repository".

After the window reloads you can start following the Quick Start below (**begin at dependency installation – cloning is already done**).

---
## 1. Quick Start (TL;DR)

Below are minimal commands for Linux (Bash). Windows / PowerShell equivalents follow.

### Linux (Ubuntu / Debian / most distros)
```bash
# 1. Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
exec "$SHELL"  # re-load shell so 'uv' is on PATH (optional)

# 2. Clone and enter the project
git clone <REPO_URL> ads_template_app
cd ads_template_app

# 3. Install dependencies (creates .venv automatically)
uv sync

# 5. Run the app
uv run streamlit run st_app.py
```

### Windows (PowerShell) – summary
```powershell
irm https://astral.sh/uv/install.ps1 | iex
git clone <REPO_URL> ads_template_app
cd ads_template_app
uv sync
uv run streamlit run st_app.py
```

Then open the URL shown (http://localhost:8501 by default). 🎉 If anything fails, see Troubleshooting.

---
## 2. Project Structure
```shell
st_app.py            # Entry point: sets layout + registers pages
gui_pages/           # Streamlit page scripts
  page1.py           # Demonstrates SQL, BigQuery, and internal API calls
  page2.py           # Placeholder
common/              # Reusable helpers
  connectivity.py    # Creates SQLAlchemy engine + BigQuery & Storage clients
  data_queries.py    # Example query functions
pyproject.toml       # Project metadata & dependencies (managed by uv)
uv.lock              # Locked, reproducible dependency versions
```

Navigation is implemented using `st.navigation([st.Page(...), ...])` in `st_app.py`.

---
## 3. Customizing the Template

| Task | Where / How |
| ---- | ----------- |
| Rename the app | Edit `[project] name`, `description` in `pyproject.toml` and title in `st_app.py` (`st.set_page_config`) |
| Remove the warning | Delete the `st.warning(...)` line in `st_app.py` |
| Add a new page | Create `gui_pages/my_new_page.py` then add `st.Page("gui_pages/my_new_page.py")` in `st_app.py` |
| Add a dependency | `uv add package_name` (commit `pyproject.toml` + `uv.lock`) |
| Remove a dependency | Remove from `pyproject.toml` then `uv sync` |
| Add internal logic | Place shared functions in `common/` |
| Update Python version | Change `requires-python` in `pyproject.toml` |


---
## 4. Data & Connectivity Explained

`common/connectivity.py` tries to create connections at import time:

* SQL Server: Chooses IAM PSC engine inside Cloud Run (detected via `K_SERVICE`) else a read engine locally.
* BigQuery: Uses Application Default Credentials (ADC) of your PC/VM.

If a SQL connection fails, it falls back to an in‑memory SQLite database and logs a warning so the app still starts.

### Example Query Flow
`page1.py` → calls `example_sql_function("NO")` → runs parameterized SQL via SQLAlchemy engine.

BigQuery example uses safe parameterization with `ScalarQueryParameter`.

Internal APIs are accessed via `sadsapi` (e.g. `get_company_info()`). These packages come from a private Artifact Registry index configured under `[tool.uv.index]` in `pyproject.toml`.

---
## 5. Tooling & Quality

### 5.1 Ruff (Linting & Formatting)
```bash
uv run ruff check .
uv run ruff format .
```

### 5.2 Pre‑commit Hooks
```bash
uv run pre-commit install
```
Hooks run automatically on `git commit`.



---
## 6. Using Jupyter Notebooks in VS Code

This template is perfect for interactive development and testing using Jupyter notebooks in VS Code. The project already includes `ipykernel` in the dev dependencies, so you can immediately start using notebooks to test queries, explore data, and prototype new features.

### 6.1 Prerequisites
- VS Code with the Python extension installed
- The project dependencies installed (`uv sync` should already be done from Quick Start)

### 6.2 Creating and Using Notebooks

1. **Create a new notebook**: In VS Code, create a new file with `.ipynb` extension (e.g., `testing.ipynb`)

2. **Select the right kernel**: When you open the notebook, VS Code should automatically detect the project's virtual environment. If not:
   - Click on the kernel selector in the top-right of the notebook
   - Choose "Select Kernel" → "Python Environments" → select the `.venv` environment from this project

3. **Import and test connectivity helpers**:
   ```python
   # Test the existing connectivity and query functions
   import sys
   sys.path.append('.')  # Ensure we can import from the project root
   
   from common.connectivity import sql_engine, bq_client, storage_client
   from common.data_queries import example_sql_function, example_bigquery_function
   import pandas as pd
   ```

4. **Run quick tests**:
   ```python
   # Test SQL connectivity and query
   df_sql = example_sql_function("NO")
   print(f"SQL query returned {len(df_sql)} rows")
   df_sql.head()
   ```
   
   ```python
   # Test BigQuery connectivity 
   df_bq = example_bigquery_function("Norway")
   print(f"BigQuery returned {len(df_bq)} rows")
   df_bq.head()
   ```

5. **Explore and prototype new queries**:
   ```python
   # Write and test new queries interactively
   from sqlalchemy import text
   
   custom_query = text("SELECT COUNT(*) as total FROM financial_forecast.mobile_network_detailed")
   result = pd.read_sql(custom_query, sql_engine)
   result
   ```

### 6.3 Best Practices for Notebook Usage

- **Keep notebooks in project root or a `notebooks/` folder**: Don't commit large notebook files or sensitive data outputs
- **Use notebooks for exploration, not production**: Move finalized code to proper Python modules in `common/` or `gui_pages/`
- **Restart kernel regularly**: Especially when testing connectivity changes or imports
- **Test with small datasets first**: Before running expensive BigQuery or SQL queries
- **Document your findings**: Use markdown cells to explain your analysis and conclusions

### 6.4 Common Notebook Patterns

**Data exploration pattern**:
```python
# Quick data profiling
df = example_sql_function("NO")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"Memory usage: {df.memory_usage().sum()} bytes")
df.describe()
```

**Query testing pattern**:
```python
# Test new query before adding to data_queries.py
from sqlalchemy import text
import streamlit as st  # For error handling pattern

@st.cache_data  # Test caching behavior
def my_new_query(param: str) -> pd.DataFrame:
    query = text("SELECT * FROM some_table WHERE column = :param")
    try:
        return pd.read_sql(query, sql_engine, params={"param": param})
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

# Test the function
result = my_new_query("test_value")
```

**API testing pattern**:
```python
# Test SADS API calls interactively
from sadsapi.financial import get_company_info

try:
    company_data = get_company_info()
    print(f"Retrieved {len(company_data)} company records")
    company_data.head()
except Exception as e:
    print(f"API call failed: {e}")
```

---
## 7. Deployment Notes (High-Level)
This template is Cloud Run friendly:
1. `Dockerfile` installs project dependencies
2. Ensure service account used by Cloud Run has the required roles (BigQuery Data Viewer, etc.).
3. Environment variable `K_SERVICE` is automatically present in Cloud Run, triggering IAM SQL engine creation.


---
## 8. Common Troubleshooting

| Problem | Symptom | Fix |
| ------- | ------- | --- |
| Private packages fail | 403 / 401 during `uv sync` | Run `uv tool install keyring --with keyrings.google-artifactregistry-auth`, `gcloud auth login` & `gcloud auth application-default login`; verify correct project; retry |
| BigQuery empty / error | Error message in UI | Confirm your access rights; run `gcloud auth application-default login` again |
| SQL query returns nothing | Empty dataframe | Check network/VPN & IAM perms; template may be falling back to SQLite (see logs) |
| Streamlit not opening | No browser | Copy the displayed URL (e.g. http://localhost:8501) into your browser manually |
| `uv` not found | Command error | Open a new terminal OR ensure install step succeeded |
| Wrong Python version | `Requires Python >=3.13` | Install Python 3.13 and re-run `uv sync` |

View logs in the terminal where you launched Streamlit for extra detail.

---
## 9. Security & Good Practices

* Never hardcode credentials in code – rely on ADC or secrets.
* Parameterize SQL (already shown with `:cc` placeholder) to avoid injection.
* Avoid printing large sensitive data frames to logs.
* Keep dependencies up to date: `uv lock --upgrade` then test.

---
## 10. Suggested Next Customization Checklist

- [ ] Change project name & description in `pyproject.toml`
- [ ] Replace homepage header / remove warning
- [ ] Remove example queries you do not need
- [ ] Add real business logic pages
- [ ] Enable pre-commit hooks
- [ ] Add tests (Pytest) if logic grows
- [ ] Set up CI (lint + app smoke test)
- [ ] Set up GCP Cloud Build

---
## 11. FAQ

**Q: Do I need to activate a virtual environment manually?**  
No – `uv run ...` and `uv sync` handle that automatically.

**Q: Can I use `pip` instead?**  
You can, but then you must manage a venv yourself. The project is optimized for `uv` (fast and reproducible).

**Q: Where do I put shared helper code?**  
In `common/` (feel free to create submodules if it grows).



---
## 12. License / Internal Use

Adapt this section to your internal licensing or usage guidelines. Remove if not relevant.

---
## 13. Support

Open an issue in the repository or contact the ADS platform team.

---
Happy building! 🚀
