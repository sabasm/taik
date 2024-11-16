import unittest
import os
from app import SpeechToTextApp, WSLAudioRecorder, WhisperTranscriber
from user_settings import Settings, SettingsButton
from unittest.mock import patch
import tempfile
from tkinter import Tk
import time

class TestSpeechToTextApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Tk()
        cls.app = SpeechToTextApp(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        if os.path.exists("session-test-session.txt"):
            os.remove("session-test-session.txt")
        if os.path.exists("user_settings.json"):
            os.remove("user_settings.json")

    def test_ui_elements(self):
        """Test UI elements without running mainloop"""
        self.assertIsNotNone(self.app.buttons["Push to Record (5s)"], "Record button should be initialized.")
        self.assertIsNotNone(self.app.buttons["Process Audio"], "Process button should be initialized.")
        self.assertIsNotNone(self.app.buttons["Delete Recording"], "Delete button should be initialized.")
        self.assertIsNotNone(self.app.buttons["Save Transcriptions"], "Save button should be initialized.")
        self.root.update()

    @patch('tkinter.messagebox.showinfo')
    def test_save_transcriptions(self, mock_showinfo):
        """Test save transcriptions functionality with mocked messagebox"""
        self.app.transcription_manager.transcriptions = ["Test transcription 1", "Test transcription 2"]
        
        self.app.save_transcriptions()
        self.root.update()

        # Verify the file contents
        with open("session-test-session.txt", "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2, "Saved file should contain all transcriptions.")
            self.assertEqual(lines[0].strip(), "Test transcription 1")
            self.assertEqual(lines[1].strip(), "Test transcription 2")

        # Verify messagebox was called
        mock_showinfo.assert_called_once()

    def test_settings_button_integration(self):
        """Test settings button integration"""
        self.assertIsNotNone(self.app.settings_button, "Settings button should be initialized")
        self.assertTrue(isinstance(self.app.settings_button, SettingsButton), 
                       "Settings button should be instance of SettingsButton")
        self.root.update()

if __name__ == "__main__":
    unittest.main()