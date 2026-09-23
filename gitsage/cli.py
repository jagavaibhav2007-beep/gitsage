"""CLI module: interactive terminal interface, option dispatching, and rich output formatting."""

import sys

# Ensure UTF-8 output on Windows terminals to support emojis and rich formatting
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from gitsage.git_tools import (
    commit_changes,
    get_staged_diff,
    get_staged_files,
    is_git_repo,
    scan_for_secrets,
)
from gitsage.reviewer import generate_commit_message, review_code

console = Console()


def _call_ai(fn, diff: str) -> str:
    """Call an AI function with unified error handling. Returns the AI response text."""
    try:
        return fn(diff)
    except ValueError as e:
        # Missing API key or config error (raised by reviewer._get_llm)
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Authentication" in error_msg:
            console.print(
                "[bold red]Authentication Error:[/bold red] Your API key is invalid. "
                "Check [bold cyan]OPENROUTER_API_KEY[/bold cyan] in [bold].env[/bold]."
            )
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            console.print(
                "[bold red]Timeout Error:[/bold red] The AI server did not respond in time. "
                "Try again or switch to a different model."
            )
        elif "Connection" in error_msg or "connect" in error_msg.lower():
            console.print(
                "[bold red]Connection Error:[/bold red] Cannot reach the AI server. "
                "Check your internet connection (or start Ollama if using local mode)."
            )
        else:
            console.print(f"[bold red]AI Error:[/bold red] {error_msg}")
        sys.exit(1)


def handle_review(diff: str):
    """Generate and display an AI code review for staged changes."""
    console.print("\n[cyan]Analyzing staged changes with AI reviewer...[/cyan]")
    review_text = _call_ai(review_code, diff)
    console.print(
        Panel(
            Markdown(review_text),
            title="[bold green]GitSage Code Review[/bold green]",
            border_style="green",
        )
    )


def handle_commit(diff: str):
    """Generate a Conventional Commit message and prompt user to commit."""
    console.print("\n[cyan]Generating Conventional Commit message...[/cyan]")
    msg = _call_ai(generate_commit_message, diff)

    console.print(
        Panel(
            f"[bold white]{msg}[/bold white]",
            title="[bold cyan]Proposed Commit Message[/bold cyan]",
            border_style="cyan",
        )
    )

    choice = console.input("[bold yellow]Accept and commit? [y/n/e(dit)]:[/] ").strip().lower()

    if choice == "y":
        success, output = commit_changes(msg)
        if success:
            console.print(f"[bold green]Committed![/bold green] {msg}")
        else:
            console.print(f"[bold red]Commit failed:[/bold red] {output}")
    elif choice in ("e", "edit"):
        custom_msg = console.input("[bold yellow]Enter your commit message:[/] ").strip()
        if custom_msg:
            success, output = commit_changes(custom_msg)
            if success:
                console.print(f"[bold green]Committed![/bold green] {custom_msg}")
            else:
                console.print(f"[bold red]Commit failed:[/bold red] {output}")
        else:
            console.print("[yellow]Empty message. Cancelled.[/yellow]")
    else:
        console.print("[yellow]Commit cancelled.[/yellow]")


def main():
    """Main CLI entrypoint for GitSage."""
    if not is_git_repo():
        console.print("[bold red]Error: Not inside a git repository.[/bold red]")
        sys.exit(1)

    diff = get_staged_diff()
    staged_files = get_staged_files()

    if not diff or not staged_files:
        console.print(
            "[yellow]No staged changes found.[/yellow]\n"
            "Use [bold cyan]git add <files>[/bold cyan] to stage your changes first."
        )
        sys.exit(0)

    # Pre-flight secret audit
    warnings = scan_for_secrets(diff, staged_files)
    if warnings:
        warning_content = "\n".join(f"  - {w}" for w in warnings)
        console.print(
            Panel(
                f"[bold red]{warning_content}[/bold red]",
                title="[bold red]Security Alert: Potential Secrets Staged[/bold red]",
                border_style="red",
            )
        )
        proceed = (
            console.input("[bold red]Secrets detected! Proceed anyway? [y/N]:[/] ")
            .strip()
            .lower()
        )
        if proceed != "y":
            console.print("[yellow]Aborted. Unstage secrets before continuing.[/yellow]")
            sys.exit(1)

    command = sys.argv[1].lower() if len(sys.argv) > 1 else "commit"

    if command == "review":
        handle_review(diff)
    elif command in ("commit", "c"):
        handle_commit(diff)
    else:
        console.print(
            f"[bold red]Unknown command:[/bold red] '{command}'\n"
            "Available: [cyan]commit[/cyan], [cyan]review[/cyan]"
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        sys.exit(0)
