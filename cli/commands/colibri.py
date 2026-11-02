"""
CLI command for Colibri local LLM management.
Uses Typer for consistency with the rest of the Charlie CLI.
"""

import typer

app = typer.Typer(help="Colibri local LLM engine management (MoE models on CPU/GPU)")


@app.command("status")
def colibri_status():
    """Show Colibri server status and available models."""
    try:
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter()
        typer.echo(adapter.status())
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)


@app.command("start")
def colibri_start(
    wait: int = typer.Option(30, "--wait", "-w", help="Seconds to wait for server to start"),
):
    """Attempt to start the Colibri LLM server."""
    try:
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter()
        result = adapter.start_server(wait_seconds=wait)
        typer.echo(result)
    except Exception as exc:
        typer.echo(f"Error starting Colibri: {exc}", err=True)
        raise typer.Exit(1)


@app.command("stop")
def colibri_stop():
    """Stop the Colibri LLM server."""
    try:
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter()
        result = adapter.stop_server()
        typer.echo(result)
    except Exception as exc:
        typer.echo(f"Error stopping Colibri: {exc}", err=True)
        raise typer.Exit(1)


@app.command("models")
def colibri_models():
    """List models available from the running Colibri server."""
    try:
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter()
        models = adapter.get_models(refresh=True)
        if not models:
            typer.echo("No models listed (server may not be running).")
        else:
            typer.echo("Available Colibri models:")
            for m in models:
                typer.echo(f"  - {m}")
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)


@app.command("chat")
def colibri_chat(
    message: str = typer.Argument(..., help="Message to send to the Colibri LLM"),
    model: str = typer.Option(None, "--model", "-m", help="Force a specific model name"),
    max_tokens: int = typer.Option(1024, "--max-tokens", help="Maximum tokens in the reply"),
    temperature: float = typer.Option(0.7, "--temp", help="Sampling temperature"),
):
    """Send a single message to the Colibri local LLM and print the reply."""
    try:
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter(model=model)
        if not adapter.is_server_running():
            typer.echo("Colibri server is not running.\n")
            typer.echo(adapter.start_guide())
            raise typer.Exit(1)
        reply = adapter.chat(message, max_tokens=max_tokens, temperature=temperature)
        typer.echo(reply)
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"Colibri chat error: {exc}", err=True)
        raise typer.Exit(1)


@app.command("help")
def colibri_help():
    """Show setup and usage guide for the Colibri LLM engine."""
    try:
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter()
        typer.echo(adapter.start_guide())
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
