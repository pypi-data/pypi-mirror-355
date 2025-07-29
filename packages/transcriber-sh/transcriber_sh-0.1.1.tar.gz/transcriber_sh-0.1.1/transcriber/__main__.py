"""
transcripter – real-time microphone → OpenAI → text
---------------------------------------------------
$ transcripter                 # record + summarise (default)
$ transcripter record          # same as above
$ transcripter list-dev        # show available mics/loopbacks
$ transcripter setup           # create / update .env (API key, model)
"""
from __future__ import annotations

import argparse, sys, os, getpass
from pathlib import Path
from textwrap import dedent

from . import audio_io
from .summarizer       import summarize
from .websocket_client import run
from .config           import MIC_ID, LOOPBACK_ID, TRANSCRIPTS


ROOT     = Path(__file__).resolve().parent.parent      # project root
ENV_FILE = ROOT / ".env"


# ────────────────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────────────────
def _write_env(api_key: str, model: str) -> None:
    """Create or update .env with OPENAI_API_KEY and MODEL."""
    entries: dict[str, str] = {}

    # keep existing unrelated vars
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                k, _, v = line.partition("=")
                entries[k.strip()] = v.strip()

    entries["OPENAI_API_KEY"] = api_key.strip()
    entries["MODEL"]          = model.strip()

    # write back
    with ENV_FILE.open("w", encoding="utf-8") as f:
        for k, v in entries.items():
            f.write(f"{k}={v}\n")

    print(f"✅  Wrote {ENV_FILE} with OPENAI_API_KEY and MODEL")


def cli() -> None:
    parser = argparse.ArgumentParser(
        prog="transcripter",
        description="Stream your mic to OpenAI and save the transcript.",
    )
    sub = parser.add_subparsers(dest="cmd")

    # record
    record_p = sub.add_parser("record", help="capture + summarise (default)")
    record_p.add_argument("--mic", type=int, default=MIC_ID, help="physical microphone index")
    record_p.add_argument("--loopback", type=int, default=LOOPBACK_ID, help="loopback device index")

    # list-dev
    sub.add_parser("list-dev", help="list all microphones/loopbacks")

    # setup
    setup_p = sub.add_parser("setup", help="create/update .env with your OpenAI key & model")
    setup_p.add_argument("--key",   help="OpenAI API key (sk-...)")
    setup_p.add_argument("--model", help="model name (default: gpt-4o-mini-transcribe)")
    setup_p.add_argument("-y", "--yes", action="store_true",
                         help="non-interactive: use provided --key / --model or defaults")

    # default command is `record`
    if len(sys.argv) == 1:
        sys.argv.append("record")

    args = parser.parse_args()

    # --------------- list-dev --------------------------------------------- #
    if args.cmd == "list-dev":
        devs = audio_io.list_devices()
        for label, dev in devs.items():
            print(f"{label}: {dev}")
            print("---------------")
        return

    # --------------- setup ------------------------------------------------ #
    if args.cmd == "setup":
        # interactive fallback
        api_key = args.key or (getpass.getpass("OpenAI API key: ") if not args.yes else "")
        while not api_key:
            api_key = getpass.getpass("OpenAI API key (cannot be empty): ")

        model = args.model or (input("Model [gpt-4o-mini-transcribe]: ").strip() if not args.yes else "")
        if not model:
            model = "gpt-4o-mini-transcribe"

        _write_env(api_key, model)
        return

    # --------------- record (default) ------------------------------------ #
    transcript: Path | None = None
    try:
        transcript = run()
    except KeyboardInterrupt:
        print("\n🛑  Shutting down…")
    finally:
        if transcript and transcript.exists():
            print("📝  Generating summary…")
            summary = summarize(transcript)
            print(f"✅  Summary written to {summary}")
        else:
            print("⚠️  No transcript captured; nothing to summarise.")


if __name__ == "__main__":
    cli()
