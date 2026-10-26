# Contributing

## Development setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,reports]"
```

## Before opening a pull request

Run the automated checks from the repository root:

```powershell
python -m pytest
python -m ruff check riskkit app tests tools
```

Keep calculation code in `riskkit`. Streamlit views should handle controls and presentation only, while reusable Plotly builders belong in `app/charts`.

New analytics behavior should include deterministic tests. Tests must not depend on network access or private credentials.

Do not commit API keys, cached downloads, virtual environments, logs, local agent files, or generated intermediate deliverables.
