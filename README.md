# ✨ Chexsa

### Your personal AI that can use your computer.

Chexsa is an open-source AI assistant that is being built to **see what is happening on your computer and take actions for you**.

Instead of only answering questions, Chexsa can work through a task step by step.

> You tell Chexsa what you want.  
> Chexsa figures out what to do next and gets to work.

---

## 🌸 What can Chexsa do?

Right now, Chexsa can use your browser.

You can ask it things like:

```text
Open Gemini and ask what the capital of the USA is.
```

```text
Open YouTube and search for a Java tutorial.
```

```text
Go to this website and fill out the form.
```

Chexsa looks at the page, decides what to do, performs the action, and looks again.

```text
You
 ↓
Chexsa
 ↓
See what is there
 ↓
Decide what to do
 ↓
Do it
 ↓
Repeat
```

No separate script needs to be written for every website.

---

## 🖥️ Desktop control

Chexsa is also learning how to use normal Windows apps.

The goal is to support requests like:

```text
Open Word and write a paragraph about AI.
```

```text
Open my document and add a new section.
```

Chexsa can already read many Windows buttons, menus, text boxes, and windows. Desktop actions are still being developed.

---

## 🚧 Current progress

| Feature | Status |
|---|---|
| Terminal chat | ✅ |
| Open websites | ✅ |
| Click and type | ✅ |
| Search websites | ✅ |
| Work with browser tabs | ✅ |
| Scroll pages | ✅ |
| Upload files | ✅ |
| Read webpage content | ✅ |
| "Hey Chexsa" voice commands | ✅ |
| Read Windows apps | 🚧 |
| Control Windows apps | 🚧 |
| Browser + desktop together | 🔜 |
| Check its own work | ✅ Browser verification |
| Learn repeated tasks | 🔜 |

Chexsa is still an early project, so some things will break while it grows.

---

## 💡 The idea

Most AI assistants work like this:

```text
You ask something
      ↓
AI answers
```

Chexsa is trying to work like this:

```text
You ask for something
        ↓
Chexsa understands the goal
        ↓
Chexsa uses your computer
        ↓
Task complete
```

The bigger goal is a personal AI that can work across websites, apps, and files instead of being limited to a chat box.

---

## 🌱 Where Chexsa is going

A future goal is for Chexsa to learn from tasks it has already completed.

Instead of figuring out the same workflow from scratch every time, it could save what worked and reuse it later.

```text
First time
Think through the task
        ↓
Task succeeds
        ↓
Save what worked
        ↓
Next time
Reuse it
```

This could make repeated tasks faster and more reliable.

---

## 🛠️ Getting Started

Chexsa currently works best on **Windows**.

### 1. Clone it

```bash
git clone https://github.com/MashrafeeAryan/Chexsa.git
cd Chexsa
```

### 2. Install it

```bash
pip install -e .
```

### 3. Add your AI provider

Create a `.env` file.

For an OpenAI-compatible provider:

```env
LLM_PROVIDER=openai_compatible
LLM_MODEL=your-model
LLM_API_KEY=your-api-key
LLM_BASE_URL=your-api-url
```

Or use Gemini:

```env
LLM_PROVIDER=gemini
LLM_MODEL=your-model
GEMINI_API_KEY=your-api-key
```

Never upload your API keys to GitHub.

### 4. Start Chexsa

```powershell
chexsa
```

Chexsa connects to Chrome on port 9222. If Chrome is not available, it starts a
separate persistent profile under `%LOCALAPPDATA%/Chexsa/chrome`. Sign into Gmail
or other websites in that profile before asking Chexsa to use them.

Type a task at `You >`. Ctrl+C cancels a running task. Exit with `exit` or `quit`.
Chrome stays open when Chexsa disconnects.

List saved tasks or resume after observing the current browser:

```powershell
chexsa --tasks
chexsa --resume TASK_ID
```

The browser engine keeps large pages locally and sends focused regions to the
model. It supports node-bound refs, search/expansion, visual fallback, verified
results, and recovery without automatically repeating uncertain submissions.
See [ARCHITECTURE.md](ARCHITECTURE.md) for settings and behavior.


---


## 🎙️ Voice Mode

Chexsa can listen for **"Hey Chexsa"** and send the rest of the sentence to the same browser agent.

Install the optional voice tools:

```powershell
pip install -e ".[voice]"
```

Start voice mode:

```powershell
chexsa-voice
```

Or start Chrome and voice mode together:

```powershell
.\scripts\start_voice.ps1
```

Then say:

```text
Hey Chexsa, search JavaScript tutorials on YouTube.
```

You can also say only **"Hey Chexsa"** and Chexsa will listen once more for your command.

Voice mode must be running to hear the wake phrase. Speech is currently transcribed with Google Speech Recognition through the SpeechRecognition package.

---

## ✅ Tests

Run the fast unit tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Run the isolated Chrome integration fixtures (no model key or real email needed):

```powershell
.\scripts\test_browser.ps1
```

GitHub Actions runs the unit and Chrome fixture tests on Python 3.11 and 3.12 for pushes and pull requests. The fixture suite includes 20 consecutive email workflows, delayed/refused/uncertain sends, large pages, frames, and visual targeting. It uses a scripted model; live Gmail and model-provider behavior require separate account-based validation. Version tags such as `v0.1.0` also build release packages automatically.

---

## 🗺️ Roadmap

```text
Browser control              ✅
        ↓
Windows app control          🚧
        ↓
Browser + desktop together
        ↓
Check whether browser actions worked ✅
        ↓
Recover when something fails
        ↓
Learn reusable tasks
        ↓
Personal memory
```

---

## ⚠️ Early Project

Chexsa is experimental.

It can interact with real websites and is being developed to control more of your computer. Avoid using it for anything where a wrong action could cause serious problems.

---

## 🤝 Contributing

Chexsa is open source and still growing.

Bug reports, ideas, experiments, and pull requests are welcome.

---

<div align="center">

### 🌸 Chexsa

**An AI that doesn't just tell you what to do.  
It helps do it.**

</div>
