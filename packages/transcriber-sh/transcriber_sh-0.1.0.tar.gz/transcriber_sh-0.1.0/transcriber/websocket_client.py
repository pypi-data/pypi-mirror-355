import json, threading, requests, websocket
from typing import Callable
from .config import BASE_URL, WS_URL, OPENAI_API_KEY, MODEL
from .config import SAMPLE_RATE, BLOCK_SIZE, CHANNELS, LOOPBACK_ID
from .paths  import next_transcript_file
from .audio_io import mic_frames
from websocket import WebSocketConnectionClosedException



def _create_client_secret() -> str:
    resp = requests.post(
        f"{BASE_URL}/realtime/transcription_sessions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}",
                 "Content-Type": "application/json"},
        json={
            "input_audio_transcription": {"language": "en", "model": MODEL}
        }
    ).json()
    print(resp)
    return resp["client_secret"]["value"]

def _save_transcript(text: str, file_path):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
        
     

def run(on_ready: Callable[[], None] | None = None) -> None:
    out_file = next_transcript_file()
    headers = [
        f"Authorization: Bearer {_create_client_secret()}",
        "OpenAI-Beta: realtime=v1",
    ]

    stop_event = threading.Event()
    def on_open(ws):
        print("✅  WebSocket opened")
        if on_ready: on_ready()

    def on_message(ws, message):
        data = json.loads(message)

        if data.get("type") == "transcription_session.created":
            # Start microphone thread once the session is live
            print("hello")
            threading.Thread(target=_stream_audio, args=(ws,stop_event), daemon=True).start()

        if data.get("type") == "conversation.item.input_audio_transcription.completed":
            transcript = data.get("transcript", "")
            _save_transcript(transcript, out_file)
            print(">", transcript)

    def on_error(_, err):
        print("❌", err)
        
        
    def on_close(ws, close_status_code, close_msg):
            stop_event.set()
            print("🔌  WebSocket closed")
        
    
    def _stream_audio(ws,stop_event):
        
        for chunk_lb, chunk_mic in mic_frames():
            if stop_event.is_set() or not ws.keep_running:
                break
            try:
                ws.send(
                    json.dumps({"type": "input_audio_buffer.append", "audio": chunk_lb})
                )
                
                
                # ws.send(
                #     json.dumps({"type": "input_audio_buffer.append", "audio": chunk_mic})
                # )
            except WebSocketConnectionClosedException:
                break

            
            
    app = websocket.WebSocketApp(
        WS_URL,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    app.run_forever()  # blocks until KeyboardInterrupt or connection close
    stop_event.set()
    return out_file