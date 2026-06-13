"""Text injector — copies text to clipboard then simulates Ctrl+V."""

from __future__ import annotations

import time


def inject(text: str) -> None:
    """Place *text* on the clipboard and paste it into the focused window."""
    if not text:
        return
    import pyperclip
    import pyautogui

    pyperclip.copy(text)
    # Brief pause so the target window can register clipboard change.
    time.sleep(0.05)
    pyautogui.hotkey("ctrl", "v")
