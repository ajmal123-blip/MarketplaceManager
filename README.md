# Marketplace Manager

Marketplace Manager is a Windows desktop application for organizing marketplace products and listings. This repository currently contains **only the project foundation**: the application shell, configuration, logging, and test setup.

No Facebook automation, account creation, OTP handling, CAPTCHA bypassing, anti-detection features, or credential storage is included.

## Technology

- Python
- PySide6 for the desktop interface
- SQLite for a future local database
- `pathlib` for safe file paths
- `python-dotenv` for local configuration
- `pytest` for automated tests
- Git for version control

## Project layout

```text
src/marketplace_manager/   Application source code
tests/                     Automated tests
data/                      Future local SQLite database location (not committed)
logs/                      Application log files (not committed)
```

## First-time setup

From PowerShell in this folder:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation scripts, run the application directly with:

```powershell
.\.venv\Scripts\python.exe -m marketplace_manager
```

## Run the application

```powershell
.\.venv\Scripts\python.exe -m marketplace_manager
```

The starter window should appear with the title “Marketplace Manager”. Close it normally when finished.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Configuration and security

Copy `.env.example` to `.env` if you need local settings. The `.env` file is excluded from Git so sensitive values are not accidentally saved in version control. Do not place passwords, API keys, tokens, or credentials in source code.

## Logging

The application writes diagnostic messages to `logs/marketplace_manager.log`. These logs are local-only and excluded from Git.

