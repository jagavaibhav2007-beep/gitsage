# GitSage 🧙‍♂️

An intelligent, terminal-native Git Commit & Security Review CLI agent.

## Overview
GitSage inspects your staged git changes, performs pre-commit security audits (detecting leaked API keys, `.env` files, and secrets), and generates standardized **Conventional Commit** messages and PR descriptions using local models (Ollama) or cloud models (OpenRouter).

## Architecture

```text
gitStage/
├── gitsage/
│   ├── __init__.py      # Package entry & versioning
│   ├── git_tools.py     # Subprocess git operations & security scanner
│   ├── reviewer.py      # LLM prompts & structured JSON output schemas
│   └── cli.py           # Terminal interface & interactive loops
├── .env.example         # Sample model & provider config
├── .gitignore           # Git ignore rules for secrets & caches
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Setup

1. **Clone or navigate to the repository**:
   ```bash
   cd gitStage
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Copy `.env.example` to `.env` and configure your preferred provider (`openrouter` or `ollama`):
   ```bash
   cp .env.example .env
   ```
