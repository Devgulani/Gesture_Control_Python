# AGENTS.md

## Project Overview

GestureOS is an AI-powered touchless computer control system that uses computer vision and hand gesture recognition to interact with a computer without traditional input devices.

The project is intended to be a professional portfolio project with clean architecture, maintainable code, and scalability for future features.

---

# Core Technologies

* Python 3.14+
* OpenCV
* MediaPipe Tasks API
* PyAutoGUI
* NumPy

Only introduce new dependencies when absolutely necessary.

---

# Architecture Rules

Before modifying any code:

* Read the existing project structure.
* Understand the current implementation.
* Reuse existing modules whenever possible.
* Avoid rewriting working code.
* Preserve backward compatibility.

Every file should have a single responsibility.

Avoid placing large amounts of logic inside `main.py`.

Keep the project modular and scalable.

---

# Coding Standards

Follow:

* PEP8
* Type hints
* OOP principles
* DRY (Don't Repeat Yourself)
* Separation of concerns
* Readable and maintainable code

Use descriptive variable and function names.

Add docstrings for public classes and methods.

Avoid magic numbers by placing configurable values inside:

```
configs/constants.py
```

---

# Existing Features

Current MVP includes:

* Real-time hand tracking
* Mouse cursor movement
* Left click
* Right click
* Scroll control
* Exit gesture
* Performance diagnostics
* Documentation

These features should not be broken by future changes.

---

# Planned Features

Future roadmap includes:

* Volume control
* Screenshot capture
* Media controls
* Presentation mode
* Gaming mode
* Custom gesture mapping
* Gesture analytics
* User profiles
* AI gesture recognition

Design new code so these features can be added without major refactoring.

---

# Performance Guidelines

Prioritize responsiveness.

Goals:

* Smooth cursor movement
* Low latency
* Stable gesture recognition
* Efficient CPU usage

Avoid unnecessary calculations every frame.

Reuse objects where possible.

Keep rendering overhead low.

---

# Documentation Rules

Whenever functionality changes, update:

* README.md
* CONTROLS.md
* DEVELOPMENT_LOG.md

Documentation should always match the implementation.

---

# Controls

Current controls are documented in:

```
CONTROLS.md
```

Whenever gestures are added, removed, or changed:

* Update CONTROLS.md
* Update README.md

Never leave documentation outdated.

---

# Git Rules

Never commit:

```
.venv/
__pycache__/
.vscode/
.idea/
assets/screenshots/
assets/models/
*.pyc
*.log
.env
```

Respect the existing `.gitignore`.

Do not modify ignore rules unless necessary.

---

# Before Implementing Features

Always:

1. Understand the existing implementation.
2. Review related modules.
3. Determine the best integration point.
4. Preserve existing functionality.
5. Minimize technical debt.

Avoid unnecessary rewrites.

---

# Testing Requirements

After every change:

* Verify the application starts.
* Verify no syntax errors exist.
* Verify existing features still work.
* Verify no regressions were introduced.

Do not assume functionality without validation.

---

# Code Quality

Prefer improving existing code over replacing it.

Keep functions focused and concise.

Avoid duplicate logic.

Favor reusable helper functions over copy-paste implementations.

---

# Decision Making

When multiple implementation approaches exist:

* Choose the most maintainable solution.
* Prefer readability over cleverness.
* Prefer scalability over short-term convenience.
* Preserve the current architecture.

If a requested change could negatively impact the project, explain the tradeoffs and propose a better alternative.

---

# Goal

Treat GestureOS as a production-quality software project rather than a tutorial.

Every contribution should improve:

* Code quality
* Maintainability
* Documentation
* Performance
* User experience
* Long-term scalability
