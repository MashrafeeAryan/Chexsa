# Chexsa

> **A personal AI that can understand what you want and work on your computer to get it done.**

Chexsa is an open-source desktop AI agent built to move beyond a normal chatbot.

The long-term goal is to create a personal AI that understands how you work, can reason through multi-step tasks, use your browser and desktop applications, check whether its actions worked, recover when something goes wrong, and eventually learn reusable skills from experience.

Instead of only telling you *how* to do something, Chexsa is being designed to actually help **do the work**.

## Vision

Most AI assistants stop at conversation.

Chexsa is meant to connect conversation with action:

```text
You describe a goal
        ↓
Chexsa understands it
        ↓
Plans the task
        ↓
Uses the browser or computer
        ↓
Checks the result
        ↓
Recovers if something failed
        ↓
Finishes the task
```

The goal is a desktop application that feels like a personal AI built around you — one that can understand your requests, work across software, remember useful context, and become better at repeated tasks over time.

## What Chexsa should become

Chexsa is being designed to eventually:

- Understand natural-language requests.
- Break larger goals into smaller steps.
- Use websites without requiring hard-coded scripts for every site.
- Control local desktop applications.
- Observe what is currently on the screen or page before acting.
- Verify that an action actually succeeded.
- Recover from unexpected pages, dialogs, or failed actions.
- Learn reusable skills from successful tasks.
- Build a personal memory of useful preferences and context.
- Give the user control over important or sensitive actions.

## What we are building now

The first major focus is **computer use**.

### Browser use

Chexsa should be able to connect to Chrome, understand unfamiliar webpages, choose useful actions, interact with page elements, and verify the result.

The goal is not to write a separate automation script for every website. Chexsa should inspect the page it is currently seeing and decide what to do from that state.

### Desktop use

Chexsa should also be able to work outside the browser.

This includes understanding and interacting with local applications, windows, files, dialogs, and other parts of the operating system.

Browser automation is the first practical surface. Desktop control will extend the same agent beyond the browser.

## Design direction

Chexsa is being built around a simple loop:

```text
Observe → Understand → Plan → Act → Verify → Recover
                                      ↑         │
                                      └─────────┘
```

Each part should stay separate enough that we can improve it without rebuilding the entire system.

Over time, successful task traces can also become reusable skills so Chexsa does not have to reason through the same workflow from scratch every time.

## Current status

Chexsa is in early development.

Right now the project has the basic Python package and terminal interface. The next development stages focus on browser control, computer-use tools, observation, action execution, and verification.

The larger memory and skill-learning systems will be added as the core computer-use agent becomes reliable.

---

Chexsa is an experiment in building a personal AI that does more than answer questions — it should be able to **understand, act, and learn**.
