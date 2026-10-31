import asyncio
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol


logger = logging.getLogger(__name__)


class InferenceError(RuntimeError):
    """Raised when local model inference cannot complete."""


class CancellationToken:
    """Thread-safe cancellation flag used by streaming generation."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


@dataclass
class ModelSettings:
    context_size: int = 2048
    threads: int = max(1, (os.cpu_count() or 2) - 1)
    batch_size: int = 128
    gpu_layers: int = 0
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 256
    timeout_seconds: int = 30


@dataclass
class ModelInfo:
    name: str
    path: Path
    size_bytes: int
    source: str
    loaded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceStats:
    load_count: int = 0
    request_count: int = 0
    error_count: int = 0
    total_latency: float = 0.0
    total_tokens: int = 0

    @property
    def average_latency(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_latency / self.request_count


class InferenceEngine(Protocol):
    def generate(
        self,
        prompt: str,
        *,
        settings: ModelSettings,
        stream_callback: Optional[Callable[[str], None]] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> str:
        ...

    def unload(self) -> None:
        ...


class LlamaCppEngine:
    """Native llama.cpp engine backed by llama-cpp-python."""

    def __init__(self, model_path: Path, settings: ModelSettings) -> None:
        self.model_path = Path(model_path)
        self.settings = settings
        self._lock = threading.RLock()
        self._llama = None
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            raise InferenceError(f"Model file not found: {self.model_path}")

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise InferenceError(
                "llama-cpp-python is not installed. Install requirements and restart."
            ) from exc

        try:
            self._llama = Llama(
                model_path=str(self.model_path),
                n_ctx=self.settings.context_size,
                n_threads=self.settings.threads,
                n_batch=self.settings.batch_size,
                n_gpu_layers=self.settings.gpu_layers,
                verbose=False,
            )
            logger.info(
                "model_loaded",
                extra={"model_path": str(self.model_path), "engine": "llama.cpp"},
            )
        except Exception as exc:
            raise InferenceError(f"Failed to load GGUF model: {exc}") from exc

    def generate(
        self,
        prompt: str,
        *,
        settings: ModelSettings,
        stream_callback: Optional[Callable[[str], None]] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> str:
        if not prompt.strip():
            return ""
        if self._llama is None:
            self._load()

        with self._lock:
            start = time.perf_counter()
            chunks: List[str] = []
            try:
                result_iter = self._llama(
                    prompt,
                    max_tokens=settings.max_tokens,
                    temperature=settings.temperature,
                    top_p=settings.top_p,
                    top_k=settings.top_k,
                    repeat_penalty=settings.repeat_penalty,
                    stream=True,
                    stop=["</s>", "ユーザー"],
                )

                timed_out = False
                for part in result_iter:
                    if time.perf_counter() - start > settings.timeout_seconds:
                        timed_out = True
                        logger.warning("inference_timeout", extra={"model_path": str(self.model_path)})
                        break
                    if cancel_token and cancel_token.cancelled:
                        logger.info("inference_cancelled", extra={"model_path": str(self.model_path)})
                        break
                    token = part.get("choices", [{}])[0].get("text", "")
                    if not token:
                        continue
                    chunks.append(token)
                    if stream_callback:
                        stream_callback(token)

                text = "".join(chunks).strip()
                if timed_out and not text:
                    raise InferenceError(
                        f"Inference timed out after {settings.timeout_seconds} seconds"
                    )
                latency = time.perf_counter() - start
                logger.info(
                    "inference_complete",
                    extra={
                        "model_path": str(self.model_path),
                        "latency_seconds": round(latency, 3),
                        "chars": len(text),
                    },
                )
                return text
            except Exception as exc:
                logger.exception("inference_failed", extra={"model_path": str(self.model_path)})
                raise InferenceError(f"llama.cpp inference failed: {exc}") from exc

    def unload(self) -> None:
        with self._lock:
            self._llama = None


class ModelManager:
    """Discovers, loads, caches, routes, and monitors local GGUF models."""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.settings = self._settings_from_config()
        self.model_dirs = self._model_dirs_from_config()
        self.routing = self.config.get("model_routing", {})
        self.models: Dict[str, ModelInfo] = {}
        self.engines: Dict[str, LlamaCppEngine] = {}
        self.stats: Dict[str, InferenceStats] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="llama")
        self._lock = threading.RLock()
        self.discover_models()

    def _settings_from_config(self) -> ModelSettings:
        return ModelSettings(
            context_size=int(self.config.get("llama.context_size", 2048)),
            threads=int(self.config.get("llama.threads", max(1, (os.cpu_count() or 2) - 1))),
            batch_size=int(self.config.get("llama.batch_size", 128)),
            gpu_layers=int(self.config.get("llama.gpu_layers", 0)),
            temperature=float(self.config.get("llama.temperature", 0.7)),
            top_p=float(self.config.get("llama.top_p", 0.9)),
            top_k=int(self.config.get("llama.top_k", 40)),
            repeat_penalty=float(self.config.get("llama.repeat_penalty", 1.1)),
            max_tokens=int(self.config.get("llama.max_tokens", 256)),
            timeout_seconds=int(self.config.get("llama.timeout_seconds", 30)),
        )

    def _model_dirs_from_config(self) -> List[Path]:
        dirs = [Path(p).expanduser() for p in self.config.get("model_directories", ["./models"])]
        if self.config.get("discover_existing_model_blobs", True):
            dirs.append(Path.home() / ".ollama" / "models" / "blobs")
        return dirs

    def discover_models(self) -> Dict[str, ModelInfo]:
        discovered: Dict[str, ModelInfo] = {}
        manifests = self._discover_blob_aliases()

        for model_dir in self.model_dirs:
            if not model_dir.exists():
                continue
            for path in model_dir.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() != ".gguf" and not self._has_gguf_header(path):
                    continue
                alias = manifests.get(path.name, path.stem)
                name = self._normalise_name(alias)
                discovered[name] = ModelInfo(
                    name=name,
                    path=path,
                    size_bytes=path.stat().st_size,
                    source="local_blob" if "sha256-" in path.name else "model_dir",
                )

        with self._lock:
            self.models = discovered
            for name in discovered:
                self.stats.setdefault(name, InferenceStats())
        logger.info("models_discovered", extra={"count": len(discovered)})
        return discovered

    def _discover_blob_aliases(self) -> Dict[str, str]:
        aliases: Dict[str, str] = {}
        manifest_root = Path.home() / ".ollama" / "models" / "manifests"
        if not manifest_root.exists():
            return aliases
        for manifest in manifest_root.rglob("*"):
            if not manifest.is_file():
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except Exception:
                continue
            model_layer = next(
                (layer for layer in data.get("layers", []) if layer.get("mediaType", "").endswith(".model")),
                None,
            )
            if not model_layer:
                continue
            digest = model_layer.get("digest", "").replace(":", "-")
            if digest:
                aliases[digest] = self._alias_from_manifest(manifest)
        return aliases

    @staticmethod
    def _alias_from_manifest(path: Path) -> str:
        parts = path.parts
        if len(parts) >= 2:
            return f"{parts[-2]}-{parts[-1]}"
        return path.stem

    @staticmethod
    def _normalise_name(name: str) -> str:
        return name.lower().replace(":", "-").replace("_", "-")

    @staticmethod
    def _has_gguf_header(path: Path) -> bool:
        try:
            with path.open("rb") as handle:
                return handle.read(4) == b"GGUF"
        except OSError:
            return False

    def list_models(self) -> List[ModelInfo]:
        return list(self.models.values())

    def resolve_model_name(self, task: str = "general") -> Optional[str]:
        configured = self.routing.get(task) or self.config.get("default_model")
        if configured:
            configured = str(configured)
            if configured.lower().endswith(".gguf"):
                configured = configured[:-5]
            normalised = self._normalise_name(configured)
            if normalised in self.models:
                return normalised
            for name in self.models:
                if normalised in name:
                    return name
        if self.models:
            return sorted(self.models.keys(), key=lambda n: self.models[n].size_bytes)[0]
        return None

    def load_model(self, name: Optional[str] = None, task: str = "general") -> LlamaCppEngine:
        model_name = self._normalise_name(name) if name else self.resolve_model_name(task)
        if not model_name or model_name not in self.models:
            available = ", ".join(sorted(self.models)) or "none"
            raise InferenceError(f"No GGUF model is configured for {task}. Available models: {available}")

        with self._lock:
            if model_name not in self.engines:
                self.engines[model_name] = LlamaCppEngine(self.models[model_name].path, self.settings)
                self.models[model_name].loaded = True
                self.stats.setdefault(model_name, InferenceStats()).load_count += 1
            return self.engines[model_name]

    def unload_model(self, name: str) -> None:
        model_name = self._normalise_name(name)
        with self._lock:
            engine = self.engines.pop(model_name, None)
            if engine:
                engine.unload()
            if model_name in self.models:
                self.models[model_name].loaded = False

    def shutdown(self) -> None:
        with self._lock:
            for engine in self.engines.values():
                engine.unload()
            self.engines.clear()
        self._executor.shutdown(wait=False, cancel_futures=True)

    def generate(
        self,
        prompt: str,
        *,
        task: str = "general",
        stream_callback: Optional[Callable[[str], None]] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> str:
        model_name = self.resolve_model_name(task)
        start = time.perf_counter()
        try:
            engine = self.load_model(model_name, task=task)
            text = engine.generate(
                prompt,
                settings=self.settings,
                stream_callback=stream_callback,
                cancel_token=cancel_token,
            )
            if model_name:
                stats = self.stats.setdefault(model_name, InferenceStats())
                stats.request_count += 1
                stats.total_latency += time.perf_counter() - start
                stats.total_tokens += max(1, len(text.split()))
            return text
        except Exception:
            if model_name:
                self.stats.setdefault(model_name, InferenceStats()).error_count += 1
            raise

    async def generate_async(
        self,
        prompt: str,
        *,
        task: str = "general",
        stream_callback: Optional[Callable[[str], None]] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.generate(
                prompt,
                task=task,
                stream_callback=stream_callback,
                cancel_token=cancel_token,
            ),
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        task: str = "general",
        stream_callback: Optional[Callable[[str], None]] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> str:
        prompt = self.format_chat_prompt(messages)
        return self.generate(
            prompt,
            task=task,
            stream_callback=stream_callback,
            cancel_token=cancel_token,
        )

    @staticmethod
    def format_chat_prompt(messages: List[Dict[str, str]]) -> str:
        rendered = []
        for message in messages:
            role = message.get("role", "user").strip().lower()
            content = message.get("content", "").strip()
            if not content:
                continue
            rendered.append(f"<|{role}>\n{content}")
        rendered.append("<|assistant>\n")
        return "\n".join(rendered)

    def generate_structured_json(
        self,
        prompt: str,
        *,
        schema: Dict[str, type],
        task: str = "general",
        retries: int = 1,
    ) -> Dict[str, Any]:
        last_error = "unknown validation error"
        for _attempt in range(retries + 1):
            raw = self.generate(prompt, task=task)
            try:
                data = json.loads(self._extract_json(raw))
                for key, expected_type in schema.items():
                    if key not in data or not isinstance(data[key], expected_type):
                        raise ValueError(f"Invalid or missing {key}")
                return data
            except Exception as exc:
                last_error = str(exc)
                logger.warning("json_validation_failed", extra={"error": last_error})
        raise InferenceError(f"Model did not return valid JSON: {last_error}")

    @staticmethod
    def _extract_json(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found")
        return text[start:end + 1]


