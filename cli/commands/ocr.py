"""
CLI command for OCR: extract text from images and scanned PDFs.
Uses Typer for consistency with the rest of the Charlie CLI.
"""

import sys
from pathlib import Path

import typer

app = typer.Typer(help="OCR: extract text from images and scanned PDF files")


@app.command("glm")
def glm_ocr_run(
    file: str = typer.Argument(..., help="Path to the image to recognise"),
    task: str = typer.Option("text", "--task", "-t", help="GLM-OCR task: text, formula, or table"),
    model_dir: Path = typer.Option(Path("models/image_to_text"), "--model-dir", help="Directory containing model.safetensors"),
    max_new_tokens: int = typer.Option(2048, min=1, help="Maximum generated tokens"),
):
    """Run the bundled GLM-OCR safetensors model on an image."""
    image = Path(file)
    if not image.is_file():
        typer.echo(f"Error: File not found: {file}", err=True)
        raise typer.Exit(1)
    task = task.lower()
    if task not in {"text", "formula", "table"}:
        typer.echo("Error: --task must be text, formula, or table.", err=True)
        raise typer.Exit(2)
    from features.ocr.glm_ocr_adapter import GLMOCRAdapter
    adapter = GLMOCRAdapter(model_dir=model_dir, strict=True, max_new_tokens=max_new_tokens)
    typer.echo(adapter.extract_text(image, task=task))


@app.command("run")
def ocr_run(
    file: str = typer.Argument(..., help="Path to the image or PDF file"),
    lang: str = typer.Option("en", "--lang", "-l", help="OCR language code (e.g. en, ch, fr, de, ja)"),
    gpu: bool = typer.Option(False, "--gpu", help="Use GPU acceleration (requires CUDA)"),
):
    """Extract text from an image or scanned PDF using PaddleOCR."""
    file_path = Path(file)
    if not file_path.exists():
        typer.echo(f"Error: File not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        adapter = PaddleOCRAdapter(lang=lang, use_gpu=gpu)
        if not adapter.available:
            typer.echo(
                "Warning: No OCR engine installed.\n"
                "  Install PaddleOCR:  pip install paddleocr paddlepaddle\n"
                "  Or pytesseract:     pip install pytesseract Pillow",
                err=True,
            )
        result = adapter.extract_text(str(file_path))
        typer.echo(result)
    except Exception as exc:
        typer.echo(f"OCR failed: {exc}", err=True)
        raise typer.Exit(1)


@app.command("info")
def ocr_info(
    lang: str = typer.Option("en", "--lang", "-l", help="Language code to check"),
    gpu: bool = typer.Option(False, "--gpu", help="Check GPU mode"),
):
    """Show OCR engine status and supported file types."""
    try:
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        adapter = PaddleOCRAdapter(lang=lang, use_gpu=gpu)
        typer.echo(adapter.describe())
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
