import base64
import soundcard as sc
from typing import Iterator, Tuple
from contextlib import ExitStack
import warnings


warnings.filterwarnings("ignore")
SAMPLERATE = 24_000
CHUNK      = 4096
def mic_frames(loopback_id: int = 1) -> Iterator[Tuple[str, str]]:
    devices   = sc.all_microphones(include_loopback=True)
    loopback  = get_default_loopback()
    mic       = sc.default_microphone()
    speaker     = sc.default_speaker()

    params = dict(samplerate=SAMPLERATE, blocksize=CHUNK, channels=1)

    with ExitStack() as stack:
        rec_lb  = stack.enter_context(loopback.recorder(**params))
        rec_mic = stack.enter_context(mic.recorder(samplerate=24_000 , channels=1))
        player  = stack.enter_context(speaker.player(samplerate=24_000,
                                                     channels=1))

        while True:
            
            lb  = rec_lb .record(numframes=CHUNK)      # shape (CHUNK,)
            mc  = rec_mic.record(numframes=CHUNK)      # shape (CHUNK,)
            # ──► ONE playback call: mix and send
            mix = (lb + mc)                    # avoid clipping
            # player.play(mix)
            # player.play(mix)

            # encode each stream separately
            pcm_lb  = (lb * 32767).clip(-32768, 32767).astype('<i2')
            pcm_mc  = (mc * 32767).clip(-32768, 32767).astype('<i2')

            yield (
                base64.b64encode(pcm_lb.tobytes()).decode('ascii'),
                base64.b64encode(pcm_mc.tobytes()).decode('ascii')
            )

# --- helpers.py  (or top of audio_io.py) ------------------------------------
import soundcard as sc

def get_default_loopback():
    """
    Return the loop-back microphone that corresponds to the *current*
    default speaker.  Works because SoundCard gives the same .id to
    the speaker and its loopback twin.

    Raises RuntimeError if no such device exists.
    """
    speaker = sc.default_speaker()
    if speaker is None:
        raise RuntimeError("No default speaker found.")

    for mic in sc.all_microphones(include_loopback=True):
        if getattr(mic, "isloopback", False) and mic.id == speaker.id:
            return mic

    # No 1-to-1 match? Pick the first loop-back as a last resort.
    for mic in sc.all_microphones(include_loopback=True):
        if getattr(mic, "isloopback", False):
            return mic

    raise RuntimeError("No loop-back microphone available on this system.")

def list_devices():
    return {
    "all" : sc.all_microphones(include_loopback=True),
    "default_input":  sc.default_microphone(),
    "default_output":  sc.default_speaker(),
    }