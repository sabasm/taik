import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import numpy as np
import whisper
import tempfile
import os
from datetime import datetime
from threading import Thread

class AudioRecorder:
    def __init__(self, samplerate=44100):
        self.samplerate = samplerate
        self.audio_data = None

    def record_audio(self, duration):
        self.audio_data = sd.rec(int(duration * self.samplerate), samplerate=self.samplerate, channels=1, dtype='float32')
        sd.wait()

    def save_to_wav(self, file_path):
        import wave
        if self.audio_data is None:
            raise ValueError("No audio recorded.")
        with wave.open(file_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes((self.audio_data * 32767).astype(np.int16).tobytes())

class Transcriber:
    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)

    def transcribe(self, file_path):
        return self.model.transcribe(file_path)["text"]

class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.audio_temp_file = None
        self.transcriptions = []
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Walkie-Talkie Speech-to-Text")
        self.root.geometry("400x400")
        self.root.resizable(False, False)

        self.history_text = tk.Text(self.root, state=tk.DISABLED, height=15, wrap=tk.WORD)
        self.history_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.record_button = tk.Button(self.root, text="Push to Record", command=self.start_recording, height=2, width=20)
        self.record_button.pack(pady=5)

        self.process_button = tk.Button(self.root, text="Process Audio", command=self.process_audio, state=tk.DISABLED, height=2, width=20)
        self.process_button.pack(pady=5)

        self.delete_button = tk.Button(self.root, text="Delete Recording", command=self.delete_audio, state=tk.DISABLED, height=2, width=20)
        self.delete_button.pack(pady=5)

        self.save_button = tk.Button(self.root, text="Save Transcriptions", command=self.save_transcriptions, state=tk.DISABLED, height=2, width=20)
        self.save_button.pack(pady=5)

    def start_recording(self):
        self.update_history("Recording started. Speak now.")
        self.record_button.config(state=tk.DISABLED)
        Thread(target=self.record_audio_thread).start()

    def record_audio_thread(self):
        try:
            self.audio_temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            self.recorder.record_audio(duration=5)
            self.recorder.save_to_wav(self.audio_temp_file.name)
            self.update_history("Recording completed. Ready to process.")
            self.process_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        except Exception as e:
            self.update_history(f"Error during recording: {e}", error=True)
        finally:
            self.record_button.config(state=tk.NORMAL)

    def process_audio(self):
        self.process_button.config(state=tk.DISABLED)
        try:
            transcription = self.transcriber.transcribe(self.audio_temp_file.name)
            self.transcriptions.append(transcription)
            self.update_history(f"Transcription: {transcription}")
            self.save_button.config(state=tk.NORMAL)
        except Exception as e:
            self.update_history(f"Error during transcription: {e}", error=True)

    def delete_audio(self):
        if self.audio_temp_file:
            os.remove(self.audio_temp_file.name)
            self.audio_temp_file = None
            self.update_history("Recording deleted. Ready to record again.")
            self.process_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def save_transcriptions(self):
        session_id = datetime.now().strftime("%d-%m-%Y-%H%M%S")
        filename = f"session-{session_id}.txt"
        with open(filename, "w") as file:
            for transcription in self.transcriptions:
                file.write(transcription + "\n")
        self.update_history(f"Transcriptions saved to {filename}")
        messagebox.showinfo("Saved", f"Session saved to {filename}")

    def update_history(self, text, error=False):
        self.history_text.config(state=tk.NORMAL)
        if error:
            self.history_text.insert(tk.END, f"Error: {text}\n", "error")
            self.history_text.tag_config("error", foreground="red")
        else:
            self.history_text.insert(tk.END, f"{text}\n", "normal")
            self.history_text.tag_config("normal", foreground="black")
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechToTextApp(root)
    root.mainloop()

