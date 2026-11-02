# Running Charlie on Windows

Charlie supports two Windows-friendly launch paths.

## Native desktop app

Use this path for the Tkinter interface, screen reading, drag-and-drop, system
tray support, local models, and a locally running Colibri server.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-windows.ps1
.\scripts\run-windows.ps1
```

Run a CLI command with:

```powershell
.\scripts\run-windows.ps1 -Mode CLI todo list
```

Place GGUF files in `models/`. Keep the GLM-OCR weight and its support files in
`models/image_to_text/`. `config.example.json` documents the local-first
defaults; it is copied to `config.json` by setup when needed.

## Docker Desktop CLI

Docker Desktop is suitable for CLI, local data, mounted GGUF models, OCR, and
document workflows. It does not run Charlie's Tkinter GUI, screen capture, or
native Windows application-launch actions.

```powershell
docker compose build
.\scripts\run-docker.ps1 version
.\scripts\run-docker.ps1 todo list
.\scripts\run-docker.ps1 chat start
```

Compose mounts `./charlie_data` at `/data` and `./models` read-only at
`/app/models`; model binaries are therefore never copied into the Docker image.
The container profile disables web search, Colibri, screen capture, Windows app
launching, and music playback by default. Edit `docker/config.json` only when
you intentionally want to enable a compatible container feature.

## Requirements

- Windows 10/11
- Python 3.10 or newer for the native path
- Docker Desktop with Linux containers for the container path
- Enough RAM/VRAM for the selected GGUF/GLM-OCR model

No cloud account is required for the native local-model path. Web research is
the explicit exception when enabled.

## Build a desktop executable

After running the native setup, create a distributable Windows desktop folder:

```powershell
.\scripts\build-windows-exe.ps1
```

The output is `dist\Charlie\Charlie.exe`. Keep the full `dist\Charlie` folder
together when moving it to another Windows system. The executable opens a
first-launch wizard before the app starts. It requires the user to select:

1. A chat `.gguf` model
2. A coding/complex `.gguf` model
3. GLM-OCR `model.safetensors`
4. Their name and occupation

The wizard writes only a per-user configuration under `%LOCALAPPDATA%\Charlie_AI`
and references models in their existing locations. It never copies model files
into the executable or sends them to a service.
