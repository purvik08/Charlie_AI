"""First-launch setup wizard for the packaged Charlie desktop application."""

from __future__ import annotations

import sys
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk


def run_first_launch_wizard(config) -> bool:
    """Collect local model paths and a small local user profile once.

    Model files are referenced in place instead of copied, avoiding duplicate
    multi-gigabyte assets. The wizard writes only to the user's local config.
    """
    if config.get("onboarding.completed", False):
        return True

    root = tk.Tk()
    wizard = _FirstLaunchWizard(root, config)
    root.mainloop()
    return wizard.completed


class _FirstLaunchWizard:
    def __init__(self, root: tk.Tk, config) -> None:
        self.root = root
        self.config = config
        self.completed = False
        self.page = 0
        self.chat_model = tk.StringVar(value=self._existing_gguf("tiny"))
        self.coding_model = tk.StringVar(value=self._existing_gguf("gemma"))
        self.image_model = tk.StringVar(value=self._existing_image_model())
        self.name = tk.StringVar(value=str(config.get("user_profile.name", "")))
        self.occupation = tk.StringVar(value=str(config.get("user_profile.occupation", "")))

        root.title("Welcome to Charlie")
        root.geometry("720x430")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self._cancel)

        self.title = ttk.Label(root, font=("Segoe UI", 16, "bold"))
        self.title.pack(anchor="w", padx=28, pady=(26, 8))
        self.subtitle = ttk.Label(root, wraplength=650, justify="left")
        self.subtitle.pack(anchor="w", padx=28, pady=(0, 16))
        self.content = ttk.Frame(root)
        self.content.pack(fill="both", expand=True, padx=28)

        footer = ttk.Frame(root)
        footer.pack(fill="x", padx=28, pady=24)
        self.back = ttk.Button(footer, text="Back", command=self._back)
        self.back.pack(side="left")
        self.next = ttk.Button(footer, text="Next", command=self._next)
        self.next.pack(side="right")
        ttk.Button(footer, text="Cancel", command=self._cancel).pack(side="right", padx=(0, 8))
        self._render()

    @staticmethod
    def _existing_gguf(keyword: str) -> str:
        model_root = _runtime_root() / "models"
        candidates = sorted(model_root.glob(f"*{keyword}*.gguf")) if model_root.exists() else []
        return str(candidates[0].resolve()) if candidates else ""

    @staticmethod
    def _existing_image_model() -> str:
        candidate = _runtime_root() / "models" / "image_to_text" / "model.safetensors"
        return str(candidate.resolve()) if candidate.is_file() else ""

    def _render(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        self.back.config(state="normal" if self.page else "disabled")
        if self.page == 0:
            self.title.config(text="1. Attach local models")
            self.subtitle.config(text=(
                "Choose the existing model files Charlie should use. Files stay where they are; "
                "Charlie stores only their local paths."
            ))
            self._file_row("Chat GGUF model", self.chat_model, [("GGUF models", "*.gguf")])
            self._file_row("Coding / complex GGUF model", self.coding_model, [("GGUF models", "*.gguf")])
            self._file_row("Image-recognition model", self.image_model, [("Safetensors model", "*.safetensors")])
            self.next.config(text="Next")
        elif self.page == 1:
            self.title.config(text="2. Tell Charlie about you")
            self.subtitle.config(text=(
                "This information stays only in your local Charlie configuration. It is used to personalize "
                "the assistant's local context."
            ))
            self._text_row("Your name", self.name)
            self._text_row("Occupation", self.occupation)
            self.next.config(text="Start Charlie")

    def _file_row(self, label: str, value: tk.StringVar, filetypes) -> None:
        row = ttk.Frame(self.content)
        row.pack(fill="x", pady=8)
        ttk.Label(row, text=label, width=30).pack(side="left")
        ttk.Entry(row, textvariable=value).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row, text="Browse…", command=lambda: self._browse(value, filetypes)).pack(side="right")

    def _text_row(self, label: str, value: tk.StringVar) -> None:
        row = ttk.Frame(self.content)
        row.pack(fill="x", pady=10)
        ttk.Label(row, text=label, width=20).pack(side="left")
        ttk.Entry(row, textvariable=value).pack(side="left", fill="x", expand=True)

    def _browse(self, value: tk.StringVar, filetypes) -> None:
        path = filedialog.askopenfilename(parent=self.root, filetypes=filetypes)
        if path:
            value.set(path)

    def _next(self) -> None:
        if self.page == 0:
            if not self._validate_model_paths():
                return
            self.page = 1
            self._render()
            return
        if not self.name.get().strip() or not self.occupation.get().strip():
            messagebox.showerror("Details required", "Enter both your name and occupation to continue.", parent=self.root)
            return
        self._save_and_start()

    def _back(self) -> None:
        if self.page:
            self.page -= 1
            self._render()

    def _validate_model_paths(self) -> bool:
        required = {
            "Chat GGUF model": self.chat_model.get(),
            "Coding / complex GGUF model": self.coding_model.get(),
            "Image-recognition model": self.image_model.get(),
        }
        for label, raw_path in required.items():
            path = Path(raw_path)
            if not path.is_file():
                messagebox.showerror("Model required", f"Select a valid file for: {label}", parent=self.root)
                return False
        if Path(self.chat_model.get()).suffix.lower() != ".gguf" or Path(self.coding_model.get()).suffix.lower() != ".gguf":
            messagebox.showerror("Invalid model", "Chat and coding models must be .gguf files.", parent=self.root)
            return False
        if Path(self.image_model.get()).name != "model.safetensors":
            messagebox.showerror("Invalid model", "Select the GLM-OCR file named model.safetensors.", parent=self.root)
            return False
        return True

    def _save_and_start(self) -> None:
        chat_path = Path(self.chat_model.get()).resolve()
        coding_path = Path(self.coding_model.get()).resolve()
        image_path = Path(self.image_model.get()).resolve()
        model_dirs = sorted({str(chat_path.parent), str(coding_path.parent)})
        self.config.config.update({
            "model_directories": model_dirs,
            "default_model": chat_path.stem,
            "model_routing": {"simple": chat_path.stem, "complex": coding_path.stem},
            "ocr_engine": "glm_ocr",
            "ocr_model_dir": str(image_path.parent),
            "user_profile": {
                "name": self.name.get().strip(),
                "occupation": self.occupation.get().strip(),
            },
            "onboarding": {"completed": True},
        })
        self.config.save_config()
        self.completed = True
        self.root.destroy()

    def _cancel(self) -> None:
        self.completed = False
        self.root.destroy()


def _runtime_root() -> Path:
    """Use PyInstaller's unpacked asset root when running as an EXE."""
    return Path(getattr(sys, "_MEIPASS", Path.cwd()))
