# syntax=docker/dockerfile:1
# Charlie's container image is for CLI/headless workflows. Run the Tkinter GUI
# natively on Windows with scripts/run-windows.ps1.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build tools are needed when pip has to compile llama-cpp-python.  espeak-ng
# keeps the optional pyttsx3 backend functional for CLI voice output.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        build-essential \
        cmake \
        espeak-ng \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install --no-deps -e .

COPY . .

# Compose supplies /app/config.json and persists Charlie's workspace at /data.
VOLUME ["/data", "/app/models"]
ENTRYPOINT ["python", "-m", "cli.main"]
CMD ["--help"]
