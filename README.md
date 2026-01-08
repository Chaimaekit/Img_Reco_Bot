# Img_Reco_Bot

A simple Tkinter utility to automate screen clicks and move a logical cursor between two grid-like positions.

It uses manual direction helper coordinates (or captured global clicks) to simulate left/right/up/down moves, supports recording arbitrary placement sequences to files, playing them back, and continuously looping a placements file until stopped.

Built with `pyautogui` for clicks and `pynput` for global click capture.

## Requirements
- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start
- Run the GUI:

```bash
python detect.py
```

- Use the GUI to:
	- Provide `Current` and `Target` positions as `x,y` in the top fields.
	- Edit direction helper constants in `detect.py` or use `Capture Directions` to record them.
	- Use `Start Diff Capture` / `Stop Capture` to record placements, `Save Placements` to write them into the `placements/` folder, and `Play Placements` or `Start Loop` to execute them.

Files without a path are placed under the `placements/` folder next to the script by default.

## Notes
- Playback and loop execution use a configurable delay (default 5s) between clicks to allow observation; adjust in the GUI.
