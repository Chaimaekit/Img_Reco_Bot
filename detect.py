import pyautogui
import time
import re
import threading
import os
import tkinter as tk
from tkinter import ttk
from pynput.mouse import Listener as GlobalMouseListener
import cv2
import numpy as np


RIGHT = (1694, 584)
LEFT = (295, 535)
UP = (952, 1)
DOWN = (997, 931)
DEFAULT_DIRECTIONS = (RIGHT, LEFT, UP, DOWN)


#function to convert various position formats to (x, y) tuple
def to_tuple(p):
    if isinstance(p, str):
        s = re.sub("[() ]", "", p)
        x, y = s.split(",")
        return (int(x), int(y))
    if hasattr(p, "x") and hasattr(p, "y"):
        return (int(p.x), int(p.y))
    if isinstance(p, (tuple, list)):
        return (int(p[0]), int(p[1]))
    raise ValueError("Unsupported position format")


def is_detected(dark_threshold=0.6, dark_pixel_tol=60):
    try:
        scr = pyautogui.screenshot()
        arr = None
        try:
            arr = np.array(scr.convert('L')) 
        except Exception:
            gray = scr.convert('L')
            arr = list(gray.getdata())
            w, h = gray.size
            arr = [arr[i * w:(i + 1) * w] for i in range(h)]
            dark = 0
            total = 0
            for row in arr:
                for v in row:
                    total += 1
                    if v < dark_pixel_tol:
                        dark += 1
            if total == 0:
                return True
            return (dark / total) < dark_threshold

        total = arr.size
        if total == 0:
            return True
        dark = int((arr < dark_pixel_tol).sum())
        dark_ratio = dark / total
        return dark_ratio < dark_threshold
    except Exception:
        return True


def move(current_pos, target_pos, directions, wait=2):

    current = to_tuple(current_pos)
    target = to_tuple(target_pos)
    right, left, up, down = directions
    # the perso appearing is stable so a pic detection should be added

    cx, cy = current
    tx, ty = target
    while (cx, cy) != (tx, ty):

        while not is_detected():
            time.sleep(wait)

        if cx < tx:
            pyautogui.click(right)
            cx += 1
            time.sleep(5)
        elif cx > tx:
            pyautogui.click(left)
            cx -= 1
            time.sleep(5)
        
        while not is_detected():
            time.sleep(wait)

        if cy < ty:
            pyautogui.click(down)
            cy += 1
            time.sleep(5)
        elif cy > ty:
            pyautogui.click(up)
            cy -= 1
            time.sleep(5)
    print("Reached the target position!")


class App:

    def __init__(self, root):
        self.root = root
        root.title("Position Controller")
        self.current_pos = None
        self.target_pos = None
        self.directions = DEFAULT_DIRECTIONS

        main = ttk.Frame(root, padding=12)
        main.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        ttk.Label(main, text="Current position:").grid(column=0, row=0, sticky=tk.W)
        self.curr_entry = ttk.Entry(main)
        self.curr_entry.grid(column=1, row=0, sticky=(tk.W, tk.E))

        ttk.Label(main, text="Target position:").grid(column=0, row=1, sticky=tk.W)
        self.targ_entry = ttk.Entry(main)
        self.targ_entry.grid(column=1, row=1, sticky=(tk.W, tk.E))

        self.dirs_label = ttk.Label(main, text=f"Directions: R{self.directions[0]} L{self.directions[1]} U{self.directions[2]} D{self.directions[3]}")
        self.dirs_label.grid(column=0, row=5, columnspan=2, sticky=tk.W)


        self.start_btn = ttk.Button(main, text="Start", command=self.start)
        self.start_btn.grid(column=0, row=3, columnspan=2, pady=(12, 0))

        self.capture_diff_btn = ttk.Button(main, text="Start Diff Capture", command=self.start_diff_capture)
        self.capture_diff_btn.grid(column=0, row=6, pady=(8, 0))
        self.stop_diff_btn = ttk.Button(main, text="Stop Capture", command=self.stop_diff_capture)
        self.stop_diff_btn.grid(column=1, row=6, pady=(8, 0))
        self.stop_diff_btn.state(['disabled'])

        self.save_diff_btn = ttk.Button(main, text="Save Placements", command=self.save_diff)
        self.save_diff_btn.grid(column=0, row=7, columnspan=2, pady=(4, 0))
        self.save_diff_btn.state(['disabled'])

        self.play_file_btn = ttk.Button(main, text="Play Placements", command=self.play_placements)
        self.play_file_btn.grid(column=0, row=8, columnspan=2, pady=(8, 0))

        ttk.Label(main, text="Filename:").grid(column=0, row=9, sticky=tk.W)
        self.diff_file_entry = ttk.Entry(main)
        self.diff_file_entry.insert(0, 'placements/placements.txt')
        self.diff_file_entry.grid(column=1, row=9, sticky=(tk.W, tk.E))

        ttk.Label(main, text="Delay (s):").grid(column=0, row=10, sticky=tk.W)
        self.delay_entry = ttk.Entry(main)
        self.delay_entry.insert(0, '6')
        self.delay_entry.grid(column=1, row=10, sticky=(tk.W, tk.E))

        self.start_loop_btn = ttk.Button(main, text="Start Loop", command=self.start_loop)
        self.start_loop_btn.grid(column=0, row=11, pady=(8, 0))
        self.stop_loop_btn = ttk.Button(main, text="Stop Loop", command=self.stop_loop)
        self.stop_loop_btn.grid(column=1, row=11, pady=(8, 0))
        self.stop_loop_btn.state(['disabled'])

        for child in main.winfo_children():
            child.grid_configure(padx=6, pady=6)


    def start_diff_capture(self):
        self._diff_clicks = []
        self.capture_diff_btn.state(['disabled'])
        self.stop_diff_btn.state(['!disabled'])
        self.save_diff_btn.state(['disabled'])
        self.dirs_label.config(text="Diff capture: click anywhere; press Stop Capture when done")

        def on_click(x, y, button, pressed):
            if not pressed:
                return
            self._diff_clicks.append((int(x), int(y)))
            count = len(self._diff_clicks)
            self.root.after(0, lambda: self.dirs_label.config(text=f"Captured diff {count} placements"))

        self._diff_listener = GlobalMouseListener(on_click=on_click)
        self._diff_listener.start()

    def stop_diff_capture(self):
        if hasattr(self, '_diff_listener') and self._diff_listener:
            try:
                self._diff_listener.stop()
            except Exception:
                pass
        self.capture_diff_btn.state(['!disabled'])
        self.stop_diff_btn.state(['disabled'])
        if hasattr(self, '_diff_clicks') and self._diff_clicks:
            self.save_diff_btn.state(['!disabled'])
            self.dirs_label.config(text=f"Captured {len(self._diff_clicks)} placements — ready to save")
        else:
            self.dirs_label.config(text="No placements captured")

    def save_diff(self, filename='placements.txt'):
        if not hasattr(self, '_diff_clicks') or not self._diff_clicks:
            self.dirs_label.config(text='No captured placements to save')
            return
        fname = self.diff_file_entry.get().strip() or filename
        path = self._resolve_placement_path(fname)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                for x, y in self._diff_clicks:
                    f.write(f"{x},{y}\n")
            self.dirs_label.config(text=f"Saved {len(self._diff_clicks)} placements to {path}")
            self.save_diff_btn.state(['disabled'])
        except Exception as e:
            self.dirs_label.config(text=f"Error saving placements: {e}")

    def start_loop(self):
        fname = self.diff_file_entry.get().strip()
        try:
            delay = float(self.delay_entry.get().strip())
        except Exception:
            delay = 5.0
        try:
            import loop_action
        except Exception as e:
            self.dirs_label.config(text=f"Cannot import loop_action: {e}")
            return
        path = self._resolve_placement_path(fname)
        ok = loop_action.start_loop(path, delay)
        if ok:
            self.start_loop_btn.state(['disabled'])
            self.stop_loop_btn.state(['!disabled'])
            self.dirs_label.config(text=f"Loop started on {path} ({delay}s)")
        else:
            self.dirs_label.config(text="Loop already running")

    def stop_loop(self):
        try:
            import loop_action
        except Exception as e:
            self.dirs_label.config(text=f"Cannot import loop_action: {e}")
            return
        loop_action.stop_loop()
        self.start_loop_btn.state(['!disabled'])
        self.stop_loop_btn.state(['disabled'])
        self.dirs_label.config(text="Loop stopped")

    def _execute_file_placements(self, filename='placements.txt'):
        path = self._resolve_placement_path(filename)
        try:
            with open(path, 'r') as f:
                lines = [ln.strip() for ln in f if ln.strip()]
        except FileNotFoundError:
            self.root.after(0, lambda: self.dirs_label.config(text=f"File not found: {path}"))
            return
        placements = []
        for ln in lines:
            try:
                x_s, y_s = ln.split(',')
                placements.append((int(x_s), int(y_s)))
            except Exception:
                continue
        if not placements:
            self.root.after(0, lambda: self.dirs_label.config(text="No valid placements in file"))
            return
        self.root.after(0, lambda: self.dirs_label.config(text=f"Executing {len(placements)} placements from {path}"))
        for i, (x, y) in enumerate(placements, start=1):
            pyautogui.click(x, y)
            time.sleep(5)
            self.root.after(0, lambda i=i: self.dirs_label.config(text=f"Executed {i}/{len(placements)}"))
        self.root.after(0, lambda: self.dirs_label.config(text="Finished executing placements"))

    def play_placements(self):
        fname = self.diff_file_entry.get().strip() or 'placements.txt'
        t = threading.Thread(target=self._execute_file_placements, args=(fname,), daemon=True)
        t.start()

    def _resolve_placement_path(self, filename):
        if os.path.isabs(filename) or os.path.dirname(filename):
            return filename
        base = os.path.dirname(os.path.abspath(__file__))
        placements_dir = os.path.join(base, 'placements')
        return os.path.join(placements_dir, filename)

    def start(self):
        cur = None
        tgt = None
        if self.current_pos:
            cur = self.current_pos
        else:
            txt = self.curr_entry.get().strip()
            if txt:
                cur = txt

        if self.target_pos:
            tgt = self.target_pos
        else:
            txt = self.targ_entry.get().strip()
            if txt:
                tgt = txt

        if not cur or not tgt:
            print("Both current and target positions must be provided (capture or enter).")
            return

        if not self.directions:
            print("Directions not captured. Please use 'Capture Directions' once before starting.")
            return

        t = threading.Thread(target=move, args=(cur, tgt, self.directions), daemon=True)
        t.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()