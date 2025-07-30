import os
import json
import pyaudio
from vosk import Model, KaldiRecognizer
from .utils import phonemes_to_letters

class STTPhonemeExtractor:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(os.getcwd(), "model")
        if not os.path.exists(model_path) or not os.listdir(model_path):
            raise FileNotFoundError(f"Vosk model folder not found or empty at: {model_path}")
        self.model = Model(model_path)

    def listen_letters_live(self):
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=16000,
                         input=True,
                         frames_per_buffer=8000)
        rec = KaldiRecognizer(self.model, 16000)
        rec.SetWords(True)
        rec.SetPartialWords(True)
        rec.SetPhones(True)

        print("🎙️ Starting letter-level live listening (Ctrl+C to stop)...")

        try:
            while True:
                data = stream.read(8000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    if 'result' in res:
                        letters_batch = []
                        for word_info in res['result']:
                            phones = word_info.get('phones', '')
                            letters = phonemes_to_letters(phones)
                            if letters:
                                spaced_letters = ' '.join(list(letters))
                                letters_batch.append(spaced_letters)
                        letters_str = ' '.join(letters_batch)
                        if letters_str.strip():
                            yield letters_str
                else:
                    pass
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
