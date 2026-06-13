# whisper-dictation

## Project Purpose
A free Windows 11 push-to-talk voice dictation app that uses local Whisper AI for transcription and injects text into any focused application. No subscriptions, no cloud API calls, no Windows native speech recognition.

## Target OS
Windows 11 (x64). The app is developed on Linux but must be fully functional on Windows 11.

## Key Requirements
- Configurable global hotkey (default: Right Ctrl held = record, release = transcribe + inject)
- Local Whisper transcription via faster-whisper (NO Windows native speech)
- Text injection via clipboard + Ctrl+V simulation (works in all apps)
- System tray icon showing recording state
- First-run model download with progress
- Config file for hotkey, Whisper model size, language

## Stack
- faster-whisper for transcription
- sounddevice + numpy for audio capture
- keyboard for global hotkeys
- pyperclip for clipboard
- pystray + Pillow for system tray
- pyautogui for Ctrl+V injection
- pyyaml for config

## Code Standards
- Python 3.11+, type hints on all public functions
- Single executable entry point: src/whisper_dictation/main.py
- requirements.txt with pinned versions
- README.md with install + usage instructions (in English AND French)
- .gitignore for Python projects

## Commands
- Run: python -m whisper_dictation
- Package: pyinstaller --onefile
