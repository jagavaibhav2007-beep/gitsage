"""Reviewer module: LangChain prompt templates and chains (Ollama & OpenRouter)."""

import os
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

# Prompt templates (lightweight, safe to define at module level)
commit_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert developer. Output ONLY a concise Conventional Commit message "
        "following 'type(scope): description' under 72 chars. "
        "Types: feat, fix, refactor, docs, chore. Do not include quotes, markdown, or explanations.",
    ),
    ("user", "Write a commit message for this git diff:\n\n{diff}"),
])

review_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a senior code reviewer. Review the git diff and provide concise feedback with bullet points:\n"
        "1. Security & Bugs\n"
        "2. Performance & Quality\n"
        "3. Suggestions\n"
        "Keep feedback brief and actionable.",
    ),
    ("user", "Review this git diff:\n\n{diff}"),
])

parser = StrOutputParser()

# Cache for the LLM instance (lazy initialization)
_llm = None


def _get_llm():
    """Initialize and cache the LangChain LLM. Validates config before creating the client."""
    global _llm
    if _llm is not None:
        return _llm

    provider = os.getenv("AI_PROVIDER", "openrouter").lower()

    if provider == "ollama":
        _llm = ChatOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model=os.getenv("OLLAMA_MODEL", "gemma4:e2b"),
            request_timeout=60,
        )
    else:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key or api_key == "your_openrouter_api_key_here":
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Add your key to .env or set AI_PROVIDER=ollama for local usage."
            )
        _llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it"),
            request_timeout=60,
        )

    return _llm


def generate_commit_message(diff: str) -> str:
    """Generate a clean Conventional Commit message from a git diff."""
    chain = commit_prompt | _get_llm() | parser
    return chain.invoke({"diff": diff}).strip()


def review_code(diff: str) -> str:
    """Provide a structured code review of the git diff."""
    chain = review_prompt | _get_llm() | parser
    return chain.invoke({"diff": diff}).strip()

