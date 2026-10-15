# 🕸️ Spider-Man Water Buddy

A cozy, transparent Windows desktop companion featuring Spider-Man hanging upside down by a web from your desktop corner to remind you to stay hydrated!

## Features
- **Transparent Desktop Corner Web-Hang**: Spider-Man hangs upside down from your top screen corner/bezel using a glowing web line with zero background obstruction.
- **Cozy & Relaxing Atmosphere**:
  - Gentle pendulum swinging animation on the web.
  - Soft glowing ambient lighting and warm, friendly superhero dialogue.
  - Dark glassmorphic card with subtle crimson and web-blue accents.
- **Dynamic Mouse Reactions**:
  - **Hover**: Move your cursor over Spider-Man and his spider-sense tingles! His eye lenses widen in friendly curiosity and he waves at you.
  - **Click & Tug (Elastic Physics)**: Click on Spider-Man or his web and drag him down or sideways. When released, an elastic spring animation snaps him back to center with realistic recoil.
- **Interactive Water Reminders**:
  - **YES**: Spider-Man celebrates with web-shooting ("Thwip!"), a thumbs up, and *"Super hydrated! Your spider-sense is at 100%! 🌟"*, auto-dismissing after 2 seconds.
  - **NO**: Spider-Man shows a funny dehydrated slump and reveals cozy **5 min**, **10 min**, and **15 min** snooze options.

## Launching the App
Run using the virtual environment:
```powershell
.\.venv\Scripts\python.exe run.py
```

## Running Automated Tests
- Offscreen unit test suite:
  ```powershell
  .\.venv\Scripts\python.exe tests\test_stage1.py
  ```
- Native Windows GUI interactive verification:
  ```powershell
  .\.venv\Scripts\python.exe tests\verify_gui.py
  ```
