"""
Create a short bullet-point summary for one transcript file and
write it next to the original (foo.txt ➜ foo.summary.txt).
"""

from pathlib import Path
import requests
from .config import OPENAI_API_KEY

_MODEL = "gpt-4.1-nano"          # keep it lightweight & cheap


def summarize(transcript_path: Path) -> Path:
    """Return the path of the summary file that was just written."""
    raw_text = transcript_path.read_text(encoding="utf-8")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type":  "application/json",
    }
    body = {
        "model": _MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise meeting assistant. "
                    "Return a bullet-point summary (max 12 bullets)."
                ),
            },
            {"role": "user", "content": raw_text},
        ],
        "temperature": 0.3,
    }

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=120,
    ).json()

    summary = resp["choices"][0]["message"]["content"].strip()

    out_file = transcript_path.with_suffix(".summary.txt")
    out_file.write_text(summary, encoding="utf-8")
    return out_file
