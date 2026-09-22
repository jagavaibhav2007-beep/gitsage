"""Reviewer module: LangChain prompt templates and chains (Ollama & OpenRouter)."""

import os
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Load settings from .env file
load_dotenv()


def get_llm():
    """Initialize LangChain LLM for Ollama (local) or OpenRouter (cloud)."""
    provider = os.getenv("AI_PROVIDER", "openrouter").lower()

    if provider == "ollama":
        return ChatOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model=os.getenv("OLLAMA_MODEL", "gemma4:e2b"),
        )

    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model=os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it"),
    )


# 1. Initialize LLM and Parser
llm = get_llm()
parser = StrOutputParser()

# 2. Conventional Commit Chain (Prompt | LLM | Parser)
commit_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert developer. Output ONLY a concise Conventional Commit message "
        "following 'type(scope): description' under 72 chars. "
        "Types: feat, fix, refactor, docs, chore. Do not include quotes, markdown, or explanations.",
    ),
    ("user", "Write a commit message for this git diff:\n\n{diff}"),
])
commit_chain = commit_prompt | llm | parser

# 3. Code Review Chain (Prompt | LLM | Parser)
review_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a senior code reviewer. Review the git diff and provide concise feedback with bullet points:\n"
        "1. 🛡️ Security & Bugs\n"
        "2. ⚡ Performance & Quality\n"
        "3. 💡 Suggestions\n"
        "Keep feedback brief and actionable.",
    ),
    ("user", "Review this git diff:\n\n{diff}"),
])
review_chain = review_prompt | llm | parser


def generate_commit_message(diff: str) -> str:
    """Generate a clean Conventional Commit message from a git diff."""
    return commit_chain.invoke({"diff": diff}).strip()


def review_code(diff: str) -> str:
    """Provide a structured code review of the git diff."""
    return review_chain.invoke({"diff": diff}).strip()

