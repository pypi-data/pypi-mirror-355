````markdown
# Transcriber

> Real-time **microphone + system-audio → OpenAI → transcript → summary** — all from a single CLI command.

---

**setup**  
  ```bash
  transcriber setup                     # prompts for API key & model – writes .env
````

– Captures the default microphone **and** the loop-back that matches your current output device.
– Works on (Pulse/ALSA).
– Streams 24 kHz PCM16 chunks; prints each finalized text fragment in the terminal.
– On Ctrl-C it saves a timestamped `.txt` transcript and generates a one-paragraph summary via OpenAI Chat.

To run


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

