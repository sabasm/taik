import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import whisper
import tempfile
import os
import sys
from datetime import datetime
from threading import Thread
import subprocess
import wave
from abc import ABC, abstractmethod
from typing import Optional, List
from config import get_config, AudioConfig, WhisperConfig, AppConfig
from user_settings import Settings, SettingsButton, AudioDeviceManager

class AudioProcessor(ABC):
    @abstractmethod
    def record_audio(self, duration: int) -> None:
        pass

    @abstractmethod
    def save_to_wav(self, file_path: str) -> None:
        pass

class TranscriptionProcessor(ABC):
    @abstractmethod
    def transcribe(self, file_path: str) -> str:
        pass

class WSLAudioRecorder(AudioProcessor):
    def __init__(self, config: AudioConfig):
        self.config = config
        self.audio_data = None

    def _build_powershell_command(self, duration: int) -> str:
        return (
            'powershell.exe -Command "'
            'Add-Type -Path \\"C:\\Program Files\\NAudio\\NAudio.dll\\"; '
            '$waveIn = New-Object NAudio.Wave.WaveInEvent; '
            '$waveIn.DeviceNumber = 0; '
            '$waveIn.WaveFormat = New-Object NAudio.Wave.WaveFormat(44100, 16, 1); '
            '$waveFile = New-Object NAudio.Wave.WaveFileWriter('
            f'\'{self.config.windows_audio_path}\', $waveIn.WaveFormat); '
            '$waveIn.DataAvailable = { param($sender, $e) '
            '$waveFile.Write($e.Buffer, 0, $e.BytesRecorded) }; '
            '$waveIn.StartRecording(); '
            f'Start-Sleep -Seconds {duration}; '
            '$waveIn.StopRecording(); '
            '$waveFile.Dispose(); '
            '$waveIn.Dispose()'
            '"'
        )
        
class WhisperTranscriber(TranscriptionProcessor):
    def __init__(self, config: WhisperConfig):
        self.config = config
        if os.environ.get('TESTING') == 'true':
            self.model = self._create_mock_model()
        else:
            self.model = whisper.load_model(self.config.model_size)

    def _create_mock_model(self):
        class MockModel:
            def transcribe(self, file_path):
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    if all(b == 0 for b in frames):
                        return {"text": ""}
                return {"text": "This is a mock transcription for testing."}
        return MockModel()

    def transcribe(self, file_path: str) -> str:
        return self.model.transcribe(file_path)["text"]

class TranscriptionManager:
    def __init__(self, file_prefix: str = "session"):
        self.transcriptions: List[str] = []
        self.file_prefix = file_prefix

    def add_transcription(self, text: str) -> None:
        self.transcriptions.append(text)

    def save_transcriptions(self, session_id: Optional[str] = None) -> str:
        if not self.transcriptions:
            raise ValueError("No transcriptions to save")

        if session_id is None:
            session_id = datetime.now().strftime("%d-%m-%Y-%H%M%S")

        filename = f"{self.file_prefix}-{session_id}.txt"
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

        with open(filename, "w") as file:
            for transcription in self.transcriptions:
                file.write(f"{transcription}\n")

        return filename

class SpeechToTextApp:
    def __init__(self, root: tk.Tk):
        self.config = get_config(testing=bool(os.environ.get('TESTING')))
        self.root = root
        self.settings = Settings()
        self.settings_button = SettingsButton(self.root, self.settings)
        self.recorder = WSLAudioRecorder(self.config.audio)
        self.transcriber = WhisperTranscriber(self.config.whisper)
        self.transcription_manager = TranscriptionManager()
        self.audio_temp_file = None
        self.buttons = {}
        self.setup_ui()
        self.setup_buttons()
        self.settings_button.pack(side=tk.TOP, pady=5)

    def setup_ui(self):
        self.root.title(self.config.app.title)
        self.root.geometry(self.config.app.geometry)
        self.root.resizable(False, False)
        self.history_text = tk.Text(
            self.root,
            state=tk.DISABLED,
            height=self.config.app.history_height,
            wrap=tk.WORD
        )
        self.history_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def setup_buttons(self):
        button_configs = [
            ("Push to Record (5s)", self.start_recording, tk.NORMAL),
            ("Process Audio", self.process_audio, tk.DISABLED),
            ("Delete Recording", self.delete_audio, tk.DISABLED),
            ("Save Transcriptions", self.save_transcriptions, tk.DISABLED)
        ]

        for text, command, initial_state in button_configs:
            button = tk.Button(
                self.root,
                text=text,
                command=command,
                height=self.config.app.button_height,
                width=self.config.app.button_width,
                state=initial_state
            )
            button.pack(pady=5)
            self.buttons[text] = button

    def start_recording(self):
        self.update_history("Recording started. Speak now.")
        self.buttons["Push to Record (5s)"].config(state=tk.DISABLED)
        Thread(target=self.record_audio_thread).start()

    def record_audio_thread(self):
        try:
            self.audio_temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            self.recorder.record_audio(duration=self.config.audio.duration)
            self.recorder.save_to_wav(self.audio_temp_file.name)
            self.update_history("Recording completed. Ready to process.")
            self.buttons["Process Audio"].config(state=tk.NORMAL)
            self.buttons["Delete Recording"].config(state=tk.NORMAL)
        except Exception as e:
            self.update_history(f"Error during recording: {e}", error=True)
        finally:
            self.buttons["Push to Record (5s)"].config(state=tk.NORMAL)

    def process_audio(self):
        self.buttons["Process Audio"].config(state=tk.DISABLED)
        try:
            transcription = self.transcriber.transcribe(self.audio_temp_file.name)
            self.transcription_manager.add_transcription(transcription)
            self.update_history(f"Transcription: {transcription}")
            self.buttons["Save Transcriptions"].config(state=tk.NORMAL)
        except Exception as e:
            self.update_history(f"Error during transcription: {e}", error=True)

    def delete_audio(self):
        if self.audio_temp_file:
            os.remove(self.audio_temp_file.name)
            self.audio_temp_file = None
            self.update_history("Recording deleted. Ready to record again.")
            self.buttons["Process Audio"].config(state=tk.DISABLED)
            self.buttons["Delete Recording"].config(state=tk.DISABLED)

    def save_transcriptions(self):
        try:
            session_id = "test-session" if os.environ.get('TESTING') else None
            filename = self.transcription_manager.save_transcriptions(session_id)
            self.update_history(f"Transcriptions saved to {filename}")
            tk.messagebox.showinfo("Saved", f"Session saved to {filename}")
        except ValueError as e:
            self.update_history("No transcriptions to save.", error=True)
        except Exception as e:
            self.update_history(f"Error saving transcriptions: {str(e)}", error=True)

    def update_history(self, text: str, error: bool = False):
        self.history_text.config(state=tk.NORMAL)
        tag = "error" if error else "normal"
        prefix = "Error: " if error else ""
        self.history_text.insert(tk.END, f"{prefix}{text}\n", tag)
        self.history_text.tag_config(tag, foreground="red" if error else "black")
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)

def main():
    config = get_config()
    if not config.run_preflight_checks():
        print("System configuration checks failed. Please check the logs.")
        sys.exit(1)
    
    root = tk.Tk()
    app = SpeechToTextApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()