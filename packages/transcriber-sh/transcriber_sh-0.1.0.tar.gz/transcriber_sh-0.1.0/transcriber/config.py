"""
Centralised, .env-driven settings for the transcripter CLI.
------------------------------------------------------------------
Priority (highest → lowest):
  1. Environment variables set in the shell
  2. Keys defined in a .env file placed in CWD or project root
  3. Hard-coded defaults below
"""

from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# ❶  Locate and load a .env file (if present)
# --------------------------------------------------------------------------- #
# We search the current working directory *first* so users can
# keep project-specific .env files outside the package.
load_dotenv()  # .env in CWD or parent dirs
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

# --------------------------------------------------------------------------- #
# ❷  Network + model
# --------------------------------------------------------------------------- #
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "Missing OPENAI_API_KEY. Set it in your shell or in a .env file."
    )

MODEL: str = os.getenv("MODEL", "gpt-4o-mini-transcribe")

INTENT   = "transcription"
BASE_URL = "https://api.openai.com/v1"
WS_URL   = f"wss://api.openai.com/v1/realtime?intent={INTENT}"

# --------------------------------------------------------------------------- #
# ❸  Audio
# --------------------------------------------------------------------------- #
# Users may override these in their .env; otherwise we fall back to originals.
SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", 24_000))
BLOCK_SIZE : int = int(os.getenv("BLOCK_SIZE" , 2_048))
CHANNELS   : int = int(os.getenv("CHANNELS"   , 1))

# Selected audio devices
MIC_ID      : int = int(os.getenv("MIC_ID")      or 0)
LOOPBACK_ID : int = int(os.getenv("LOOPBACK_ID") or 1)
# --------------------------------------------------------------------------- #
# ❹  Paths
# --------------------------------------------------------------------------- #
ROOT         = Path(__file__).resolve().parent.parent
TRANSCRIPTS  = ROOT / "transcripts"
TRANSCRIPTS.mkdir(exist_ok=True)
