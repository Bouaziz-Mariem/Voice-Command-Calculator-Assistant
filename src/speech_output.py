"""
Speech Output Module
Speaks results aloud using pyttsx3 (offline text-to-speech engine).
Uses a singleton engine to avoid conflicts from multiple initializations.

Example:
    speak(format_result(1081))  →  speaks "The answer is 1081"
"""

import pyttsx3

_engine = None


def _get_engine():
    """Initialize the TTS engine once and reuse it."""
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 160)     # words per minute (160 = natural)
        _engine.setProperty("volume", 0.9)   # 0.0 to 1.0
    return _engine


def speak(text: str):
    """
    Speak the given text aloud. Blocks until speech finishes.

    Args:
        text: The string to speak.
    """
    engine = _get_engine()
    engine.say(text)
    engine.runAndWait()


def format_result(result: float | int) -> str:
    """
    Format a numeric result into a speakable sentence.

    Examples:
        format_result(20)     → "The answer is 20"
        format_result(10.0)   → "The answer is 10"
        format_result(3.1416) → "The answer is 3.142"
    """
    # If the result is a whole number, display as int (no ".0")
    if isinstance(result, float) and result == int(result):
        return f"The answer is {int(result)}"
    # Otherwise show up to 4 significant figures
    if isinstance(result, float):
        return f"The answer is {result:.4g}"
    return f"The answer is {result}"
