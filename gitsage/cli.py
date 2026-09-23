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


def handle_review(diff: str):
    """Generate and display an AI code review for staged changes."""
    console.print("\n[cyan]🔍 Analyzing staged changes with AI reviewer...[/cyan]")
    try:
        review_text = review_code(diff)
    except Exception as e:
        if "401" in str(e) or "Authentication" in str(e):
            console.print(
                "[bold red]❌ Authentication Error:[/bold red] Please add your valid "
                "[bold cyan]OPENROUTER_API_KEY[/bold cyan] in [bold].env[/bold] "
                "(or set [bold cyan]AI_PROVIDER=ollama[/bold cyan] to run locally)."
            )
        else:
            console.print(f"[bold red]❌ Error communicating with AI:[/bold red] {e}")
        sys.exit(1)

    console.print(
        Panel(
            Markdown(review_text),
            title="[bold green]GitSage Code Review[/bold green]",
            border_style="green",
        )
    )


def handle_commit(diff: str):
    """Generate a Conventional Commit message and prompt user to commit."""
    console.print("\n[cyan]🤖 Generating Conventional Commit message...[/cyan]")
    try:
        msg = generate_commit_message(diff)
    except Exception as e:
        if "401" in str(e) or "Authentication" in str(e):
            console.print(
                "[bold red]❌ Authentication Error:[/bold red] Please add your valid "
                "[bold cyan]OPENROUTER_API_KEY[/bold cyan] in [bold].env[/bold] "
                "(or set [bold cyan]AI_PROVIDER=ollama[/bold cyan] to run locally)."
            )
        else:
            console.print(f"[bold red]❌ Error communicating with AI:[/bold red] {e}")
        sys.exit(1)

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
            console.print(f"[bold green]✔ Committed successfully![/bold green] ({msg})")
        else:
            console.print(f"[bold red]❌ Commit failed:[/bold red] {output}")
    elif choice in ("e", "edit"):
        custom_msg = console.input("[bold yellow]Enter your custom commit message:[/] ").strip()
        if custom_msg:
            success, output = commit_changes(custom_msg)
            if success:
                console.print(f"[bold green]✔ Committed successfully![/bold green] ({custom_msg})")
            else:
                console.print(f"[bold red]❌ Commit failed:[/bold red] {output}")
        else:
            console.print("[yellow]Empty commit message. Cancelled.[/yellow]")
    else:
        console.print("[yellow]Commit cancelled.[/yellow]")


def main():
    """Main CLI entrypoint for GitSage."""
    if not is_git_repo():
        console.print("[bold red]❌ Error: Not inside a git repository.[/bold red]")
        sys.exit(1)

    diff = get_staged_diff()
    staged_files = get_staged_files()

    if not diff or not staged_files:
        console.print(
            "[yellow]⚠️ No staged changes found.[/yellow]\n"
            "Use [bold cyan]git add <files>[/bold cyan] to stage your changes first."
        )
        sys.exit(0)

    # Pre-flight secret audit
    warnings = scan_for_secrets(diff, staged_files)
    if warnings:
        warning_content = "\n".join(f"• {w}" for w in warnings)
        console.print(
            Panel(
                f"[bold red]{warning_content}[/bold red]",
                title="[bold red]⚠️ Security Alert: Potential Secrets Staged[/bold red]",
                border_style="red",
            )
        )
        proceed = (
            console.input("[bold red]Potential secrets detected! Do you still want to proceed? [y/N]:[/] ")
            .strip()
            .lower()
        )
        if proceed != "y":
            console.print("[yellow]Aborted for safety. Unstage secrets before continuing.[/yellow]")
            sys.exit(1)

    command = sys.argv[1].lower() if len(sys.argv) > 1 else "commit"

    if command == "review":
        handle_review(diff)
    elif command in ("commit", "c"):
        handle_commit(diff)
    else:
        console.print(
            f"[bold red]Unknown command:[/bold red] '{command}'. Available commands: [cyan]commit[/cyan], [cyan]review[/cyan]"
        )


if __name__ == "__main__":
    main()

