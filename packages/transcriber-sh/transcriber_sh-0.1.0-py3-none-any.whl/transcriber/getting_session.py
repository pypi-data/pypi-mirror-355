import json
import os
import threading
import soundcard as sc
import numpy as np
import base64
import websocket
import requests




def out_path():
    import re
    OUT_DIR = "transcripts"
    os.makedirs(OUT_DIR, exist_ok=True)

    # look for existing files named like “0001.txt”, “0002.txt”, …
    serial_re = re.compile(r"^(\d+)\.txt$")
    existing  = [
        int(m.group(1))
        for f in os.listdir(OUT_DIR)
        if (m := serial_re.match(f))
    ]
    next_serial = (max(existing) + 1) if existing else 1
    return os.path.join(OUT_DIR, f"{next_serial:04d}.txt")


OUT_PATH = out_path()


def token():
    r = "https://api.openai.com/v1/realtime/transcription_sessions"
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    headers = {
        "Authorization": "Bearer " + OPENAI_API_KEY,
        "Content-Type":"application/json"
    }
    data = {
        "input_audio_transcription": {
            "language":"en",
            "model" :"gpt-4o-mini-transcribe",
            
        }
    }
    r = requests.post(r, headers=headers,json=data).json()


    return r.get("client_secret").get("value")





def record_and_stream(ws):
    mic = sc.all_microphones(include_loopback=True)[1]
    default_speaker = sc.default_speaker()
    
    with mic.recorder(samplerate=24_000, blocksize=2048, channels=1) as rec, default_speaker.player(samplerate=24_000) as sp :
        while True:
            floats = rec.record(numframes=24_000)
            pcm16 = (floats * 32767.0) \
                      .clip(-32768, 32767) \
                      .astype('<i2')
            b64 = base64.b64encode(pcm16.tobytes()).decode('ascii')
            print(b64)
            ws.send(json.dumps({
                "type":  "input_audio_buffer.append",
                "audio": b64
            }))

def on_open(ws):
    print("Connected to server.")
    
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "transcription_session.created":
        print(data)

        threading.Thread(target=record_and_stream, args=(ws,)).start()
    
    if data.get("type") == "conversation.item.input_audio_transcription.completed":
        transcript = data.get("transcript", "").strip()
        with open(OUT_PATH, "a", encoding="utf-8") as f:
            f.write(transcript + "\n")
        print("::::::", data.get("transcript"))

def on_error(ws, message):
    print(message)







if "__main__" == __name__:
    weird_headers = [
        "Authorization: Bearer " + token(),
        "OpenAI-Beta: realtime=v1"
    ]
    URL = "wss://api.openai.com/v1/realtime?intent=transcription"    
    ws = websocket.WebSocketApp(
        URL,
        header=weird_headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
    )
    try:
        ws.run_forever()
    except KeyboardInterrupt:
        raise