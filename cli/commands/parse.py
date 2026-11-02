"""
CLI command for document parsing: convert documents to Markdown/text via Docling.
Uses Typer for consistency with the rest of the Charlie CLI.
"""

from pathlib import Path

import typer

app = typer.Typer(help="Parse documents (PDF, DOCX, PPTX, XLSX, HTML, EPUB, …) into Markdown or text")


@app.command("run")
def parse_run(
    source: str = typer.Argument(..., help="Local file path or URL to parse"),
    fmt: str = typer.Option(
        "markdown",
        "--format", "-f",
        help="Output format: 'markdown' or 'text'",
    ),
    summary: bool = typer.Option(
        False,
        "--summary", "-s",
        help="Print only a short ~200-word preview",
    ),
    output: str = typer.Option(
        None,
        "--output", "-o",
        help="Save output to this file instead of printing",
    ),
):
    """Parse a document and print (or save) its text content."""
    try:
        from features.document_parser.docling_adapter import DoclingAdapter
        adapter = DoclingAdapter(output_format=fmt)

        if summary:
            result = adapter.get_summary(source, max_words=200)
        else:
            result = adapter.convert(source)

        if output:
            out_path = Path(output)
            out_path.write_text(result, encoding="utf-8")
            typer.echo(f"Saved to {out_path}")
        else:
            typer.echo(result)
    except Exception as exc:
        typer.echo(f"Document parsing failed: {exc}", err=True)
        raise typer.Exit(1)


@app.command("info")
def parse_info(
    fmt: str = typer.Option("markdown", "--format", "-f", help="Output format"),
):
    """Show supported document formats and parser status."""
    try:
        from features.document_parser.docling_adapter import DoclingAdapter
        adapter = DoclingAdapter(output_format=fmt)
        typer.echo(adapter.describe())
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
