"""Runs Chexsa with the "Hey Chexsa" wake phrase.
It sends Word-writing commands to desktop automation and other commands to the browser.
Voice mode is optional and does not change the normal terminal mode."""

from agent import Agent
from browser_actions import BrowserActions
from browser_state import BrowserState
from desktop_actions import DesktopActions
from llm import LLM


WAKE_PHRASE = "hey chexsa"


def extract_command(text: str) -> str | None:
    """Return the words spoken after the wake phrase."""

    clean_text = text.strip()
    lower_text = clean_text.lower()

    if not lower_text.startswith(WAKE_PHRASE):
        return None

    return clean_text[len(WAKE_PHRASE):].lstrip(" ,.!?:-")


def create_browser_agent(llm: LLM) -> tuple[BrowserState, Agent]:
    """Connect the existing browser agent for voice commands."""

    browser = BrowserState()
    browser.connect()

    actions = BrowserActions(
        browser.get_page,
        browser.set_page,
    )

    agent = Agent(
        observe=browser.observe,
        decide=llm.decide,
        execute=actions.execute,
    )

    return browser, agent


def is_word_write_command(command: str) -> bool:
    """Check whether a command asks Chexsa to write in Word."""

    words = command.lower()
    writing_words = ("write", "draft", "create", "type")

    return "word" in words and any(
        word in words
        for word in writing_words
    )


def run_command(
    command: str,
    browser_agent: Agent,
    llm: LLM,
    desktop: DesktopActions,
) -> str:
    """Send the command to Word automation or the browser agent."""

    if is_word_write_command(command):
        text = llm.generate_text(command)
        desktop.write_word(text)
        return "I wrote it in Word."

    return browser_agent.run(command)


def main() -> None:
    """Listen for Hey Chexsa and run the spoken browser command."""

    try:
        import speech_recognition as sr
    except ImportError as error:
        raise RuntimeError(
            'Voice mode is not installed. Run: pip install -e ".[voice]"'
        ) from error

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    llm = LLM()
    desktop = DesktopActions()
    browser, agent = create_browser_agent(llm)

    print('Chexsa Voice')
    print('Say "Hey Chexsa" followed by a command.')
    print('Press Ctrl+C to stop.\n')

    try:
        with microphone as source:
            print("Calibrating microphone...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for Hey Chexsa...")

            while True:
                audio = recognizer.listen(
                    source,
                    phrase_time_limit=10,
                )

                try:
                    text = recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as error:
                    print(f"Chexsa > Speech service error: {error}")
                    continue

                command = extract_command(text)

                if command is None:
                    continue

                if not command:
                    print("Chexsa > What should I do?")
                    audio = recognizer.listen(
                        source,
                        phrase_time_limit=10,
                    )

                    try:
                        command = recognizer.recognize_google(audio).strip()
                    except sr.UnknownValueError:
                        print("Chexsa > I did not understand that.")
                        continue
                    except sr.RequestError as error:
                        print(f"Chexsa > Speech service error: {error}")
                        continue

                if command.lower() in {"exit", "quit", "stop listening"}:
                    print("Chexsa > Goodbye.")
                    break

                print(f"You > {command}")
                response = run_command(
                    command,
                    agent,
                    llm,
                    desktop,
                )
                print(f"Chexsa > {response}")
                print("Listening for Hey Chexsa...")

    except KeyboardInterrupt:
        print("\nChexsa > Goodbye.")

    finally:
        browser.close()


if __name__ == "__main__":
    main()
