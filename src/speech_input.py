"""
Speech Input Module
Captures microphone audio and converts it to text using Google's speech recognition API.
"""

import speech_recognition as sr


def listen(noise_duration=1.0, timeout=5, phrase_time_limit=10) -> str | None:
    """
    Listen to the microphone and return recognized text as a lowercase string.

    Args:
        noise_duration: Seconds to calibrate for ambient noise before listening.
        timeout: Max seconds to wait for speech to begin.
        phrase_time_limit: Max seconds of speech to record.

    Returns:
        Recognized text (lowercase) or None if recognition failed.
    """
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            # Calibrate to filter out background noise
            recognizer.adjust_for_ambient_noise(source, duration=noise_duration)
            print("Listening...")
            audio = recognizer.listen(source, timeout=timeout,
                                      phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        print("No speech detected within timeout.")
        return None
    except OSError as e:
        print(f"Microphone error: {e}")
        return None

    # Send audio to Google speech recognition
    try:
        text = recognizer.recognize_google(audio)
        return text.lower()
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"Speech recognition API error: {e}")
        return None
