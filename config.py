import os
import sys
import platform
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

@dataclass
class AudioConfig:
    samplerate: int = 44100
    channels: int = 1
    sample_width: int = 2
    duration: int = 5
    windows_audio_path: str = ''
    wsl_path: str = '/tmp/recording.wav'

    def __post_init__(self):
        if not self.windows_audio_path:
            # Use Public folder for reliability
            self.windows_audio_path = 'C:\\Users\\Public\\wsl_recording.wav'
        
        # Ensure NAudio is installed
        setup_script = os.path.join(os.path.dirname(__file__), 'setup_audio.ps1')
        with open(setup_script, 'w') as f:
            f.write(setup_script_content)  # This would be the content from setup_audio.ps1
        
        try:
            subprocess.run(['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', setup_script], 
                         check=True)
        except subprocess.CalledProcessError as e:
            if not os.environ.get('TESTING'):
                raise RuntimeError("Failed to setup audio capture.") from e
                
@dataclass
class WhisperConfig:
    model_size: str = "base"
    language: Optional[str] = None
    task: str = "transcribe"
    device: Optional[str] = None

@dataclass
class AppConfig:
    title: str = "WSL2 Speech-to-Text"
    geometry: str = "400x400"
    history_height: int = 15
    button_height: int = 2
    button_width: int = 20

class SystemConfiguration:
    def __init__(self):
        self.audio = AudioConfig()
        self.whisper = WhisperConfig()
        self.app = AppConfig()
        self.logger = self._setup_logger()
        self._environment_checks = []
        self._dependency_checks = []
        self._setup_checks()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SpeechToText')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _setup_checks(self):
        # Environment checks
        self._environment_checks.extend([
            (self._check_wsl, "WSL2 environment check"),
            (self._check_display, "X11 display check"),
            (self._check_temp_dir, "Temporary directory check")
        ])

        # Dependency checks
        self._dependency_checks.extend([
            (self._check_powershell, "PowerShell accessibility check"),
            (self._check_python_packages, "Python package check"),
            (self._check_ffmpeg, "FFmpeg installation check")
        ])

    def _check_wsl(self) -> bool:
        try:
            return 'microsoft' in platform.uname().release.lower()
        except:
            return False

    def _check_display(self) -> bool:
        return bool(os.environ.get('DISPLAY'))

    def _check_temp_dir(self) -> bool:
        temp_dir = Path('/tmp')
        return temp_dir.exists() and os.access(temp_dir, os.W_OK)

    def _check_powershell(self) -> bool:
        try:
            subprocess.run(['powershell.exe', '-Command', 'echo test'], 
                         capture_output=True, check=True)
            return True
        except:
            return False

    def _check_python_packages(self) -> bool:
        required_packages = ['numpy', 'whisper', 'torch']
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            self.logger.error(f"Missing packages: {', '.join(missing_packages)}")
            return False
        return True

    def _check_ffmpeg(self) -> bool:
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False

    def run_preflight_checks(self) -> bool:
        """Run all preflight checks and return True if all pass."""
        self.logger.info("Starting preflight checks...")
        
        all_passed = True
        
        self.logger.info("Checking environment...")
        for check, description in self._environment_checks:
            try:
                if not check():
                    self.logger.error(f"Failed: {description}")
                    all_passed = False
                else:
                    self.logger.info(f"Passed: {description}")
            except Exception as e:
                self.logger.error(f"Error during {description}: {str(e)}")
                all_passed = False

        self.logger.info("Checking dependencies...")
        for check, description in self._dependency_checks:
            try:
                if not check():
                    self.logger.error(f"Failed: {description}")
                    all_passed = False
                else:
                    self.logger.info(f"Passed: {description}")
            except Exception as e:
                self.logger.error(f"Error during {description}: {str(e)}")
                all_passed = False

        if all_passed:
            self.logger.info("All preflight checks passed!")
        else:
            self.logger.error("Some preflight checks failed!")
            
        return all_passed

    def get_testing_config(self) -> 'SystemConfiguration':
        """Return a configuration suitable for testing."""
        self.whisper.model_size = "tiny"
        self.audio.duration = 1
        return self

def get_config(testing: bool = False) -> SystemConfiguration:
    """Get system configuration, optionally configured for testing."""
    config = SystemConfiguration()
    return config.get_testing_config() if testing else config