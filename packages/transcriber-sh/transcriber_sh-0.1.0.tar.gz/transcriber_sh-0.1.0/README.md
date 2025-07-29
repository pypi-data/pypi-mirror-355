````markdown
# Transcriber

> Real-time **microphone + system-audio → OpenAI → transcript → summary** — all from a single CLI command.

---

* **One-step setup**  
  ```bash
  transcriber setup                     # prompts for API key & model – writes .env
````

* **Automatic device routing**
  – Captures the default microphone **and** the loop-back that matches your current output device (no index hunting).
  – Works on Windows, macOS, Linux (Pulse/ALSA).

* **Realtime transcription** (OpenAI Realtime API)
  – Streams 24 kHz PCM16 chunks; prints each finalized text fragment in the terminal.

* **Instant summary**
  – On Ctrl-C it saves a timestamped `.txt` transcript and generates a one-paragraph summary via OpenAI Chat.

* **Pure Python, no drivers** – uses `soundcard` + `sounddevice` for audio I/O.

---

## 🔧 Quick-start

```bash
# 1. install
pip install transcriber          # or: pip install git+https://github.com/Dogmeat0/transcriber.git

# 2. initial configuration
transcriber setup                # enter your OpenAI API key and choose model

# 3. record!
transcriber                      # press Ctrl-C to stop & get summary
```

| Command                                         | What it does                                               |
| ----------------------------------------------- | ---------------------------------------------------------- |
| `transcriber list-dev`                          | Lists all microphones / loop-backs & the current defaults. |


```dotenv
OPENAI_API_KEY = sk-************************************
MODEL          = gpt-4o-mini-transcribe


```bash
git clone https://github.com/Dogmeat0/transcriber.git
cd transcriber
python -m venv env && source env/bin/activate
pip install -e ".[dev]"             # editable + dev tools
ruff check transcriber              # lint
pytest                               # tests (if/when added)
```

