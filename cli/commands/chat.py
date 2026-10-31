"""Interactive chat mode for Charlie."""

import typer
from rich.console import Console
from rich.panel import Panel

from ..core import get_assistant, shutdown_assistant
from ..utils import warning

app = typer.Typer(name="chat", help="Interactive chat mode.", rich_markup_mode="rich")
console = Console()


@app.command("start")
def start(
    voice: bool = typer.Option(
        None, "--voice/--no-voice", help="Use voice (TTS) for responses."
    ),
) -> None:
    """Start an interactive chat session with Charlie."""
    assistant = get_assistant()

    if not assistant.tts:
        warning("TTS is not available; responses will be text-only.")
        use_voice = False
    elif voice is None:
        answer = console.input(
            "[cyan]Use voice for responses? [bold](y/N)[/bold]: [/cyan]"
        ).strip().lower()
        use_voice = answer in ("y", "yes")
    else:
        use_voice = voice

    if use_voice:
        success_voice(assistant)

    console.print(
        Panel(
            "[bold cyan]Charlie Chat[/bold cyan]\n"
            "Type your message. Commands: /exit, /quit, /clear, /help, /voice",
            border_style="cyan",
        )
    )

    try:
        while True:
            try:
                user_input = console.input("[bold green]You:[/bold green] ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Goodbye![/yellow]")
                break

            if not user_input:
                continue

            if user_input in ("/exit", "/quit", "exit", "quit"):
                console.print("[yellow]Goodbye![/yellow]")
                break

            if user_input == "/clear":
                assistant.conversation_history.clear()
                console.print("[yellow]History cleared[/yellow]")
                continue

            if user_input == "/help":
                console.print(
                    "Commands: /exit, /quit, /clear, /help, /voice\n"
                    "Ask about time, date, system info, battery, files, notes, "
                    "todos, reminders, or open apps."
                )
                continue

            if user_input == "/voice":
                use_voice = not use_voice
                console.print(
                    f"[yellow]Voice is now {'on' if use_voice else 'off'}[/yellow]"
                )
                continue

            with console.status("[cyan]Thinking...[/cyan]"):
                response = assistant.submit_command(user_input)

            console.print(
                Panel(response, title="[bold blue]Charlie[/bold blue]", border_style="blue")
            )

            if use_voice and assistant.tts:
                try:
                    assistant.speak(response)
                except Exception as exc:
                    warning(f"TTS failed: {exc}")
    finally:
        shutdown_assistant()


def success_voice(assistant) -> None:
    from ..utils import success

    success("Voice responses enabled")