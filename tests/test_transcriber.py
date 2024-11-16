import unittest
from app import WhisperTranscriber
from config import WhisperConfig
import tempfile
import wave
import os

class TestTranscriber(unittest.TestCase):
    def setUp(self):
        config = WhisperConfig(model_size="tiny")
        self.transcriber = WhisperTranscriber(config)
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(self.temp_file.name, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b'\x00\x00' * 44100)  # 1 second of silence

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_transcribe_silence(self):
        transcription = self.transcriber.transcribe(self.temp_file.name)
        self.assertIsInstance(transcription, str, "Transcription result should be a string.")
        self.assertEqual(transcription.strip(), "", "Transcription of silence should be empty.")

if __name__ == "__main__":
    unittest.main()