"""System information commands for Charlie."""

import typer

app = typer.Typer(name="system", help="System information commands.", rich_markup_mode="rich")


@app.command("info")
def system_info() -> None:
    """Show basic system information."""
    from core.assistant import SystemInfo
    from rich.console import Console
    from rich.table import Table

    console = Console()
    info = SystemInfo.get_system_info()

    def human_bytes(size):
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.1f} {unit}"
            size /= 1024

    rows = [
        ("System", info.get("system")),
        ("Hostname", info.get("node")),
        ("Release", info.get("release")),
        ("Machine", info.get("machine")),
        ("Processor", info.get("processor")),
        ("CPU Count", info.get("cpu_count")),
        ("CPU Usage", f"{info.get('cpu_usage')}%"),
        ("Memory Total", human_bytes(info.get("memory_total") or 0)),
        ("Memory Available", human_bytes(info.get("memory_available") or 0)),
    ]
    table = Table(title="System Information", header_style="bold cyan")
    table.add_column("Key")
    table.add_column("Value")
    for key, value in rows:
        table.add_row(key, str(value))
    console.print(table)


@app.command("battery")
def battery() -> None:
    """Show battery status."""
    from core.assistant import SystemInfo
    from rich.console import Console

    console = Console()
    battery_info = SystemInfo.get_battery_info()
    if not battery_info:
        console.print("[yellow]Battery information not available[/yellow]")
        raise typer.Exit(1)
    console.print(
        f"[cyan]Battery:[/cyan] {battery_info['percent']}% "
        f"({'charging' if battery_info['power_plugged'] else 'discharging'})"
    )


if __name__ == "__main__":
    app()