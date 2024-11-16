import unittest
from app import WSLAudioRecorder
from config import AudioConfig
import tempfile
import os

class TestAudioRecorder(unittest.TestCase):
    def setUp(self):
        config = AudioConfig()  # Use default config for testing
        self.recorder = WSLAudioRecorder(config)
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_record_audio(self):
        self.recorder.record_audio(1)  # Record 1 second of audio
        self.assertIsNotNone(self.recorder.audio_data, "Audio data should not be None after recording.")

    def test_save_to_wav(self):
        self.recorder.record_audio(1)  # Record 1 second of audio
        self.recorder.save_to_wav(self.temp_file.name)
        self.assertTrue(os.path.exists(self.temp_file.name), "WAV file should exist after saving.")

if __name__ == "__main__":
    unittest.main()