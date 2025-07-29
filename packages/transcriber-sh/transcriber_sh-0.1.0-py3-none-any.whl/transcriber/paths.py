from pathlib import Path
import re

OUT_DIR = Path("transcripts")
_OUT_RE = re.compile(r"^(\d+)\.txt$")

def next_transcript_file() -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    existing = [
        int(m.group(1))
        for m in (_OUT_RE.match(f.name) for f in OUT_DIR.iterdir())
        if m
    ]
    serial = max(existing, default=0) + 1
    return OUT_DIR / f"{serial:04d}.txt"
