"""Local GLM-OCR adapter backed by ``models/image_to_text/model.safetensors``.

The repository includes the small Hugging Face configuration, processor, tokenizer,
and prompt-template files. Only the large weight file is excluded. If a custom
model directory is incomplete, the adapter can download its missing support files
once and keeps them beside the weights for later local use.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional, Union

from .paddleocr_adapter import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, PaddleOCRAdapter

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_MODEL_DIR = _PROJECT_ROOT / "models" / "image_to_text"
MODEL_FILE = "model.safetensors"
MODEL_REPOSITORY = "zai-org/GLM-OCR"
SUPPORT_FILES = (
    "config.json",
    "generation_config.json",
    "preprocessor_config.json",
    "processor_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
)

TASK_PROMPTS = {
    "text": "Text Recognition:",
    "formula": "Formula Recognition:",
    "table": "Table Recognition:",
}


class GLMOCRAdapter:
    """Run GLM-OCR locally, loading the 2.65 GB model only when needed.

    ``fallback`` is used for PDFs and when ``strict`` is false and the optional
    GLM-OCR runtime cannot be prepared.  This preserves the existing OCR
    experience on machines where Torch/Transformers are not installed yet.
    """

    def __init__(
        self,
        model_dir: Optional[Union[str, Path]] = None,
        *,
        fallback: Optional[PaddleOCRAdapter] = None,
        strict: bool = False,
        max_new_tokens: int = 2048,
    ) -> None:
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self.fallback = fallback
        self.strict = strict
        self.max_new_tokens = max_new_tokens
        self._model = None
        self._processor = None
        self._load_error: Optional[str] = None

    @property
    def weights_path(self) -> Path:
        return self.model_dir / MODEL_FILE

    @property
    def available(self) -> bool:
        """True when local GLM-OCR weights are present."""
        return self.weights_path.is_file()

    @property
    def engine_name(self) -> str:
        return "GLM-OCR" if self.available else "none"

    def describe(self) -> str:
        if not self.available:
            return (
                f"GLM-OCR weights were not found at {self.weights_path}. "
                "Use PaddleOCR instead or place model.safetensors in that directory."
            )
        missing = [name for name in SUPPORT_FILES if not (self.model_dir / name).is_file()]
        status = "ready" if not missing else "will download model support files on first use"
        return (
            f"OCR powered by GLM-OCR ({status}).\n"
            f"Model: {self.weights_path}\n"
            "Image tasks: text, formula, table. PDFs use the configured fallback OCR engine."
        )

    def extract_text(
        self,
        source: Union[str, Path],
        *,
        task: str = "text",
        prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
    ) -> str:
        """Recognise an image using one of GLM-OCR's documented prompts.

        A custom prompt is intended for the model's supported JSON-schema based
        information extraction workflow.  For normal OCR use ``task='text'``.
        """
        path = Path(source)
        if not path.is_file():
            return f"File not found: {source}"
        if path.suffix.lower() in DOCUMENT_EXTENSIONS:
            return self._fallback_or_message(
                path,
                "GLM-OCR accepts image inputs; use the existing OCR engine for PDFs.",
            )
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            return f"Unsupported image type: {path.suffix or '(no extension)'}"
        if task not in TASK_PROMPTS and not prompt:
            return "Unsupported GLM-OCR task. Choose one of: text, formula, table."
        if not self.available:
            return self._fallback_or_message(
                path,
                f"GLM-OCR weights were not found at {self.weights_path}.",
            )

        try:
            self._load()
            instruction = prompt.strip() if prompt else TASK_PROMPTS[task]
            return self._generate(path, instruction, max_new_tokens or self.max_new_tokens)
        except Exception as exc:
            self._load_error = str(exc)
            logger.exception("GLM-OCR failed for %s", path)
            return self._fallback_or_message(path, f"GLM-OCR failed: {exc}")

    def _fallback_or_message(self, path: Path, message: str) -> str:
        if self.fallback is not None and not self.strict:
            logger.info("%s Falling back to %s.", message, self.fallback.engine_name)
            return self.fallback.extract_text(path)
        return (
            f"{message}\n"
            "Install the GLM-OCR runtime with: "
            "pip install 'transformers>=5.3.0' torch accelerate safetensors huggingface_hub"
        )

    def _load(self) -> None:
        if self._model is not None and self._processor is not None:
            return
        self._ensure_support_files()
        try:
            import torch
            from transformers import AutoModelForImageTextToText, AutoProcessor
        except ImportError as exc:
            raise RuntimeError(
                "GLM-OCR requires transformers, torch, accelerate, safetensors, and huggingface_hub."
            ) from exc

        # ``device_map='auto'`` uses CUDA when available and keeps CPU-only
        # environments functional. It requires Accelerate, declared as an
        # optional dependency in requirements.txt.
        kwargs = {"torch_dtype": "auto", "device_map": "auto", "local_files_only": True}
        try:
            self._processor = AutoProcessor.from_pretrained(self.model_dir, local_files_only=True)
            self._model = AutoModelForImageTextToText.from_pretrained(self.model_dir, **kwargs)
        except Exception:
            # Avoid retaining a partly loaded model after an out-of-memory or
            # incompatible-runtime failure.
            self._model = None
            self._processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise

    def _ensure_support_files(self) -> None:
        missing = [name for name in SUPPORT_FILES if not (self.model_dir / name).is_file()]
        if not missing:
            return
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise RuntimeError(
                "Model support files are missing. Install huggingface_hub or add "
                + ", ".join(missing)
                + f" from {MODEL_REPOSITORY} to {self.model_dir}."
            ) from exc

        self.model_dir.mkdir(parents=True, exist_ok=True)
        for filename in missing:
            cached = Path(hf_hub_download(repo_id=MODEL_REPOSITORY, filename=filename))
            shutil.copy2(cached, self.model_dir / filename)
        logger.info("Downloaded GLM-OCR support files to %s", self.model_dir)

    def _generate(self, image_path: Path, instruction: str, max_new_tokens: int) -> str:
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "url": str(image_path.resolve())},
                {"type": "text", "text": instruction},
            ],
        }]
        inputs = self._processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        inputs.pop("token_type_ids", None)
        inputs = inputs.to(self._model.device)
        generated = self._model.generate(**inputs, max_new_tokens=max_new_tokens)
        prompt_tokens = inputs["input_ids"].shape[1]
        output = self._processor.decode(generated[0][prompt_tokens:], skip_special_tokens=True).strip()
        if not output:
            return f"No content detected in image: {image_path.name}"
        return f"**GLM-OCR Result — {image_path.name}**\n\n{output}"
