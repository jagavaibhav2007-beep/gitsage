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

   In `.env`:
   ```env
   # AI Provider: 'openrouter' (cloud) or 'ollama' (local)
   AI_PROVIDER=openrouter

   # OpenRouter Settings
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=google/gemma-4-26b-a4b-it

   # Ollama Settings (if AI_PROVIDER=ollama)
   OLLAMA_MODEL=gemma4:e2b
   ```

## Available Commands

Stage your changes first:
```bash
git add <files>
```

Then run GitSage commands:

### 1. `commit` (Default)
Generates a Conventional Commit message based on your staged git diff, displays a preview, and lets you accept, edit, or cancel before committing.

```bash
python -m gitsage
# or explicitly:
python -m gitsage commit
# or shortcut:
python -m gitsage c
```

**Interactive Options:**
- `y`: Commit immediately with the generated message.
- `e` / `edit`: Enter your own custom commit message.
- `n`: Abort and discard the commit.

### 2. `review`
Performs an AI-powered code review on your staged diff, categorizing findings into:
- 🛡️ **Security & Bugs**
- ⚡ **Performance & Quality**
- 💡 **Suggestions**

```bash
python -m gitsage review
```

---

## Pre-commit Security Audit

Before sending any diff to an AI model or committing, GitSage automatically scans staged files and newly added diff lines for:
- Leaked tokens & API keys (OpenAI keys, GitHub tokens, hardcoded passwords)
- Sensitive files being staged (e.g. `.env`, `.pem`, `.key`)

If potential secrets are found, an alert panel is shown with an option to abort and unstage immediately.
