"""Small standard-library client for Ollama's local chat API."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    pass


class OllamaVisionAdapter:
    def __init__(self, *, base_url: str = "http://127.0.0.1:11434", model: str = "moondream",
                 timeout_seconds: float = 60, max_total_image_bytes: int = 16 * 1024 * 1024):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if (isinstance(max_total_image_bytes, bool) or not isinstance(max_total_image_bytes, int)
                or max_total_image_bytes <= 0):
            raise ValueError("max_total_image_bytes must be a positive integer")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_total_image_bytes = max_total_image_bytes

    def analyze(self, image_paths: list[Path], prompt: str) -> str:
        try:
            total_size = sum(path.stat().st_size for path in image_paths)
        except OSError as exc:
            raise OllamaError(f"could not inspect image: {exc}") from exc
        if total_size > self.max_total_image_bytes:
            raise OllamaError(
                f"selected images total {total_size} bytes; limit is {self.max_total_image_bytes} bytes"
            )
        raw_images = []
        remaining = self.max_total_image_bytes
        try:
            for path in image_paths:
                with path.open("rb") as image_file:
                    image = image_file.read(remaining + 1)
                if len(image) > remaining:
                    raise OllamaError(
                        f"selected images exceed the {self.max_total_image_bytes}-byte total limit"
                    )
                raw_images.append(image)
                remaining -= len(image)
        except OSError as exc:
            raise OllamaError(f"could not read image: {exc}") from exc
        images = [base64.b64encode(image).decode("ascii") for image in raw_images]
        body = json.dumps({
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [{"role": "user", "content": prompt, "images": images}],
            "options": {"temperature": 0},
        }).encode("utf-8")
        request = Request(self.base_url + "/api/chat", data=body,
                          headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise OllamaError(f"Ollama returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise OllamaError(f"Ollama is unavailable or timed out: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OllamaError("Ollama returned invalid JSON") from exc
        try:
            content = payload["message"]["content"]
        except (TypeError, KeyError) as exc:
            raise OllamaError("Ollama response did not contain message.content") from exc
        if not isinstance(content, str):
            raise OllamaError("Ollama message.content was not text")
        return content
