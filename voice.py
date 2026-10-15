"""Runs Chexsa with the "Hey Chexsa" wake phrase.
It routes each request to the browser agent or desktop agent.
Voice mode is optional and does not change the normal terminal mode."""

from agent import Agent
from browser_actions import BrowserActions
from browser_state import BrowserState
from desktop_actions import DesktopActions
from desktop_state import DesktopState
from llm import LLM


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


def create_desktop_agent(llm: LLM) -> Agent:
    """Connect the existing desktop state and actions to the agent loop."""

    state = DesktopState()
    actions = DesktopActions()

    return Agent(
        observe=state.observe,
        decide=llm.decide_desktop,
        execute=actions.execute,
    )


def run_command(
    command: str,
    browser_agent: Agent,
    desktop_agent: Agent,
    llm: LLM,
) -> str:
    """Route the command to the browser or desktop agent."""

    if llm.choose_mode(command) == "desktop":
        return desktop_agent.run(command)

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
    browser, browser_agent = create_browser_agent(llm)
    desktop_agent = create_desktop_agent(llm)

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
                response = run_command(
                    command,
                    browser_agent,
                    desktop_agent,
                    llm,
                )
                print(f"Chexsa > {response}")
                print("Listening for Hey Chexsa...")

    except KeyboardInterrupt:
        print("\nChexsa > Goodbye.")

    finally:
        browser.close()


if __name__ == "__main__":
    main()
