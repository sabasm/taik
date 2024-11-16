import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from tkinter import Tk
from user_settings import Settings, AudioDeviceManager, SettingsWindow, SettingsButton
from pathlib import Path

class TestSettings(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_settings.json")
        self.settings = Settings(self.config_file)

    def tearDown(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        try:
            os.rmdir(self.temp_dir)
        except:
            pass

    def test_save_and_load(self):
        test_device = "TEST-DEVICE-1"
        test_folder = "/test/folder"
        
        self.settings.set("audio_device", test_device)
        self.settings.set("session_folder", test_folder)
        
        new_settings = Settings(self.config_file)
        self.assertEqual(new_settings.get("audio_device"), test_device)
        self.assertEqual(new_settings.get("session_folder"), test_folder)

    def test_default_settings(self):
        settings = Settings()
        self.assertEqual(settings.get("audio_device"), "")
        self.assertEqual(
            settings.get("session_folder"),
            str(Path.home() / "transcription_sessions")
        )
        self.assertIsNone(settings.get("last_session"))

class TestAudioDeviceManager(unittest.TestCase):
    @patch('subprocess.run')
    def test_get_audio_devices(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps([
            {"Name": "Test Device 1", "DeviceID": "TEST-1"},
            {"Name": "Test Device 2", "DeviceID": "TEST-2"}
        ])
        mock_run.return_value = mock_result
        
        manager = AudioDeviceManager()
        devices = manager.get_audio_devices()
        
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["Name"], "Test Device 1")
        self.assertEqual(devices[1]["DeviceID"], "TEST-2")

    def test_get_audio_devices_testing_mode(self):
        os.environ['TESTING'] = 'true'
        manager = AudioDeviceManager()
        devices = manager.get_audio_devices()
        
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["Name"], "Test Microphone 1")
        self.assertEqual(devices[1]["DeviceID"], "TEST-2")

class TestSettingsWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Tk()
        cls.settings = Settings()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        if os.path.exists("user_settings.json"):
            os.remove("user_settings.json")

    def setUp(self):
        self.window = SettingsWindow(self.root, self.settings)

    def test_window_creation(self):
        self.assertIsNotNone(self.window)
        self.assertEqual(self.window.window.title(), "Settings")

    @patch('tkinter.filedialog.askdirectory')
    def test_browse_folder(self, mock_askdirectory):
        test_path = "/test/path"
        mock_askdirectory.return_value = test_path
        self.window.browse_folder()
        self.assertEqual(self.settings.get("session_folder"), test_path)

    def test_device_change(self):
        with patch.object(self.window.device_manager, 'get_audio_devices') as mock_devices:
            mock_devices.return_value = [
                {"Name": "Test Device", "DeviceID": "TEST-ID"}
            ]
            self.window.device_var.set("Test Device")
            self.window.on_device_change(None)
            self.assertEqual(self.settings.get("audio_device"), "TEST-ID")

class TestSettingsButton(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.settings = Settings()
        self.button = SettingsButton(self.root, self.settings)

    def tearDown(self):
        self.root.destroy()
        if os.path.exists("user_settings.json"):
            os.remove("user_settings.json")

    def test_button_creation(self):
        self.assertIsNotNone(self.button)
        self.assertEqual(self.button["text"], "⚙️")

    @patch('user_settings.SettingsWindow')
    def test_open_settings(self, mock_window):
        self.button.open_settings()
        mock_window.assert_called_once_with(self.root, self.settings)

if __name__ == '__main__':
    unittest.main()