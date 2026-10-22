"""Runs Chexsa with the "Hey Chexsa" wake phrase.
It routes each request to chat, the browser agent, or the desktop agent.
Voice mode is optional and does not change the normal terminal mode."""

from app_runtime import AppSession


WAKE_PHRASE = "hey chexsa"


def extract_command(text: str) -> str | None:
    """Return the words spoken after the wake phrase."""

    clean_text = text.strip()
    lower_text = clean_text.lower()

    if not lower_text.startswith(WAKE_PHRASE):
        return None

    return clean_text[len(WAKE_PHRASE):].lstrip(" ,.!?:-")


def listen_text(recognizer, source, sr) -> str | None:
    """Listen once and return recognized speech."""

    audio = recognizer.listen(source, phrase_time_limit=10)

    try:
        return recognizer.recognize_google(audio).strip()
    except sr.UnknownValueError:
        return None
    except sr.RequestError as error:
        print(f"Chexsa > Speech service error: {error}")
        return None


def main() -> None:
    """Listen for Hey Chexsa and route the spoken request."""

    try:
        import speech_recognition as sr
    except ImportError as error:
        raise RuntimeError(
            'Voice mode is not installed. Run: pip install -e ".[voice]"'
        ) from error

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    app = AppSession()

    print('Chexsa Voice')
    print('Say "Hey Chexsa" followed by a command.')
    print('Press Ctrl+C to stop.\n')

    try:
        with microphone as source:
            print("Calibrating microphone...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for Hey Chexsa...")

            while True:
                text = listen_text(recognizer, source, sr)

                if not text:
                    continue

                command = extract_command(text)

                if command is None:
                    continue

                if not command:
                    print("Chexsa > What should I do?")
                    command = listen_text(recognizer, source, sr)

                    if not command:
                        print("Chexsa > I did not understand that.")
                        continue

                if command.lower() in {"exit", "quit", "stop listening"}:
                    print("Chexsa > Goodbye.")
                    break

                print(f"You > {command}")
                try:
                    print(f"Chexsa > {app.run(command)}")
                except Exception as error:
                    print(f"Chexsa > Could not run the request: {error}")
                print("Listening for Hey Chexsa...")

    except KeyboardInterrupt:
        print("\nChexsa > Goodbye.")

    finally:
        app.close()


if __name__ == "__main__":
    main()
