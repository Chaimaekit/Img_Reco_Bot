import threading
import time
import pyautogui

_running = False
_thread = None
_lock = threading.Lock()


def _run_loop(filename, delay):
    global _running
    while _running:
        try:
            with open(filename, 'r') as f:
                lines = [ln.strip() for ln in f if ln.strip()]
        except Exception:
            time.sleep(1)
            continue
        placements = []
        for ln in lines:
            try:
                x_s, y_s = ln.split(',')
                placements.append((int(x_s), int(y_s)))
            except Exception:
                continue
        if not placements:
            time.sleep(1)
            continue
        for x, y in placements:
            if not _running:
                break
            try:
                pyautogui.click(x, y)
            except Exception:
                pass
            time.sleep(delay)


def start_loop(filename='placements.txt', delay=5):
    """Start looping execution of placements in `filename` every `delay` seconds.
    Returns True if loop started, False if already running.
    """
    global _running, _thread
    with _lock:
        if _running:
            return False
        _running = True
        _thread = threading.Thread(target=_run_loop, args=(filename, delay), daemon=True)
        _thread.start()
        return True


def stop_loop():
    global _running
    with _lock:
        _running = False


def is_running():
    return _running
