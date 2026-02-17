import ctypes
import time
import math
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

import win32con
import win32gui
import win32process
import psutil

import mss
import numpy as np

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

GAME_PID = 13496 #Change this by going to task manager -> details -> find roblox and copy its PID. This way the script knows which window is roblox. 
WIN_X, WIN_Y = 50, 50
WIN_W, WIN_H = 900, 800

START_WORD = "tales" #Starting word. Tales is statistically the best possible choice. 
LETTER_DELAY_S = 0.3

TOTAL_POST_ENTER_WAIT_S = 5.0

MAX_ROWS = 6

PLAY_AGAIN_CLIENT = (504, 416)
PLAY_AGAIN_HEX = "#136F05"
PLAY_AGAIN_TOL = 35

INVALID_TOAST_CLIENT = (441, 163)
INVALID_BASELINE_HEX = "#0F0F10"
INVALID_TOL = 25
INVALID_POLL_INTERVAL_S = 0.05
INVALID_POLL_TOTAL_S = 1.2
INVALID_SAMPLE_R = 1

BACKSPACE_COUNT = 7
BACKSPACE_DELAY_S = 0.3

REJECTS_FILE = "rejects.txt"

AHK_PRIMARY_MODE = "SendInput"
AHK_CANDIDATES = [
    r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
    r"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe",
    r"C:\Program Files\AutoHotkey\AutoHotkey64.exe",
    r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
    "AutoHotkey64.exe",
    "AutoHotkey.exe",
]

POINTS: List[Tuple[int, int]] = [
    (285, 155), (353, 154), (420, 156), (486, 156), (552, 155),
    (284, 221), (352, 223), (417, 222), (487, 221), (555, 221),
    (285, 285), (353, 288), (420, 288), (486, 288), (552, 288),
    (286, 354), (353, 354), (420, 355), (487, 353), (552, 354),
    (284, 422), (350, 422), (418, 422), (486, 421), (553, 421),
    (287, 490), (353, 489), (420, 488), (488, 486), (555, 486),
]
ROWS, COLS = 6, 5

def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.strip().lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def rgb_to_bgr(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return (rgb[2], rgb[1], rgb[0])

RGB_GREY = hex_to_rgb("#313134")
RGB_ORANGE = hex_to_rgb("#A58C1C")
RGB_GREEN = hex_to_rgb("#31A134")

BGR_GREY = rgb_to_bgr(RGB_GREY)
BGR_ORANGE = rgb_to_bgr(RGB_ORANGE)
BGR_GREEN = rgb_to_bgr(RGB_GREEN)

BGR_PLAY = rgb_to_bgr(hex_to_rgb(PLAY_AGAIN_HEX))
BGR_INVALID_BASELINE = rgb_to_bgr(hex_to_rgb(INVALID_BASELINE_HEX))

REF = {"b": BGR_GREY, "y": BGR_ORANGE, "g": BGR_GREEN}

def dist3(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)

def classify_bgr(bgr: Tuple[int, int, int]) -> str:
    return min(REF.keys(), key=lambda k: dist3(bgr, REF[k]))

def set_window_rect(hwnd: int, x: int, y: int, w: int, h: int):
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, w, h, win32con.SWP_SHOWWINDOW)

def activate_window(hwnd: int):
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.05)

def get_client_rect_on_screen(hwnd: int) -> Tuple[int, int, int, int]:
    l, t, r, b = win32gui.GetClientRect(hwnd)
    w, h = r - l, b - t
    sx, sy = win32gui.ClientToScreen(hwnd, (0, 0))
    return sx, sy, w, h

def client_to_screen(hwnd: int, cx: int, cy: int) -> Tuple[int, int]:
    sx, sy = win32gui.ClientToScreen(hwnd, (cx, cy))
    return int(sx), int(sy)

def click_client(hwnd: int, cx: int, cy: int):
    sx, sy = client_to_screen(hwnd, cx, cy)
    ctypes.windll.user32.SetCursorPos(sx, sy)
    time.sleep(0.02)
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.02)
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.05)

def find_main_hwnd_by_pid(pid: int) -> Optional[int]:
    candidates = []

    def enum_cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        try:
            _, wpid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:
            return
        if wpid != pid:
            return
        try:
            l, t, r, b = win32gui.GetClientRect(hwnd)
            area = max(0, (r - l) * (b - t))
        except Exception:
            area = 0
        if area < 20_000:
            return
        title = (win32gui.GetWindowText(hwnd) or "").strip()
        candidates.append((area, hwnd, title))

    win32gui.EnumWindows(enum_cb, None)
    if not candidates:
        return None
    candidates.sort(reverse=True, key=lambda x: x[0])
    area, hwnd, title = candidates[0]
    print(f"[FOUND] pid={pid} hwnd={hwnd} title={title!r} client_area={area}")
    return hwnd

def capture_client_bgr(hwnd: int, sct: mss.mss) -> np.ndarray:
    x, y, w, h = get_client_rect_on_screen(hwnd)
    shot = sct.grab({"left": x, "top": y, "width": w, "height": h})
    return np.array(shot)[:, :, :3]

def avg_patch_bgr(frame: np.ndarray, cx: int, cy: int, r: int = 3) -> Tuple[int, int, int]:
    h, w = frame.shape[:2]
    x0 = max(0, cx - r)
    x1 = min(w - 1, cx + r)
    y0 = max(0, cy - r)
    y1 = min(h - 1, cy + r)
    patch = frame[y0:y1 + 1, x0:x1 + 1].reshape(-1, 3).mean(axis=0)
    return (int(round(patch[0])), int(round(patch[1])), int(round(patch[2])))

def read_row_feedback(hwnd: int, row_idx: int, sct: mss.mss) -> str:
    frame = capture_client_bgr(hwnd, sct)
    start = row_idx * COLS
    out = []
    for i in range(COLS):
        cx, cy = POINTS[start + i]
        bgr = avg_patch_bgr(frame, cx, cy, r=3)
        out.append(classify_bgr(bgr))
    return "".join(out)

def should_click_play_again(hwnd: int, sct: mss.mss) -> bool:
    frame = capture_client_bgr(hwnd, sct)
    cx, cy = PLAY_AGAIN_CLIENT
    got = avg_patch_bgr(frame, cx, cy, r=2)
    return dist3(got, BGR_PLAY) <= PLAY_AGAIN_TOL

def invalid_toast_triggered(hwnd: int, sct: mss.mss) -> bool:
    polls = max(1, int(round(INVALID_POLL_TOTAL_S / INVALID_POLL_INTERVAL_S)))
    for _ in range(polls):
        frame = capture_client_bgr(hwnd, sct)
        cx, cy = INVALID_TOAST_CLIENT
        got = avg_patch_bgr(frame, cx, cy, r=INVALID_SAMPLE_R)
        if dist3(got, BGR_INVALID_BASELINE) > INVALID_TOL:
            return True
        time.sleep(INVALID_POLL_INTERVAL_S)
    return False

def sleep_remaining_after_toast_check():
    remaining = max(0.0, TOTAL_POST_ENTER_WAIT_S - INVALID_POLL_TOTAL_S)
    if remaining > 0:
        time.sleep(remaining)

def load_words(path: str = "wordlist.txt") -> List[str]:
    words = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            w = line.strip().lower()
            if len(w) == 5 and w.isalpha():
                words.append(w)
    return sorted(set(words))

def append_reject(word: str):
    with open(REJECTS_FILE, "a", encoding="utf-8") as f:
        f.write(word + "\n")

def feedback_for(solution: str, guess: str) -> str:
    res = ["b"] * 5
    sol = list(solution)
    g = list(guess)

    for i in range(5):
        if g[i] == sol[i]:
            res[i] = "g"
            sol[i] = None
            g[i] = None

    for i in range(5):
        if g[i] is None:
            continue
        if g[i] in sol:
            res[i] = "y"
            sol[sol.index(g[i])] = None

    return "".join(res)

def filter_candidates(cands: List[str], guess: str, observed: str) -> List[str]:
    return [w for w in cands if feedback_for(w, guess) == observed]

def pick_next_guess(candidates: List[str], allowed: List[str], used: set) -> Optional[str]:
    freq = {}
    for w in candidates:
        for ch in set(w):
            freq[ch] = freq.get(ch, 0) + 1

    def score(w: str) -> int:
        return sum(freq.get(ch, 0) for ch in set(w))

    best = None
    best_score = -1
    for w in candidates:
        if w in used:
            continue
        s = score(w)
        if s > best_score:
            best_score = s
            best = w
    if best:
        return best

    best = None
    best_score = -1
    for w in allowed:
        if w in used:
            continue
        s = score(w)
        if s > best_score:
            best_score = s
            best = w
    return best

def find_ahk_exe() -> Optional[str]:
    for p in AHK_CANDIDATES:
        if (":" in p) or p.startswith("\\"):
            if os.path.exists(p):
                return p
        else:
            return p
    return None

def build_ahk_script_for_hwnd(hwnd: int, guess: str, letter_delay_s: float, mode: str) -> str:
    send_fn = "SendInput" if mode.lower() == "sendinput" else "SendEvent"
    delay_ms = int(round(letter_delay_s * 1000))
    safe_guess = guess.replace('"', '""')

    return f"""
#Requires AutoHotkey v2.0
#SingleInstance Force

hwnd := {hwnd}
guess := "{safe_guess}"
delay := {delay_ms}

WinActivate "ahk_id " hwnd
WinWaitActive "ahk_id " hwnd, , 2

Loop Parse guess {{
    {send_fn} A_LoopField
    Sleep delay
}}
{send_fn} "{{Enter}}"

ExitApp 0
""".strip()

def ahk_send_guess(hwnd: int, guess: str, mode: str) -> bool:
    ahk_exe = find_ahk_exe()
    if not ahk_exe:
        print("[ERROR] AutoHotkey v2 executable not found.")
        return False

    script_path = Path.cwd() / "_wordle_send.ahk"
    script_path.write_text(build_ahk_script_for_hwnd(hwnd, guess, LETTER_DELAY_S, mode), encoding="utf-8")

    try:
        p = subprocess.run([ahk_exe, str(script_path)], timeout=15)
        return p.returncode == 0
    except Exception as e:
        print(f"[ERROR] AHK run failed: {e}")
        return False

def submit_guess(hwnd: int, guess: str):
    activate_window(hwnd)
    ok = ahk_send_guess(hwnd, guess, AHK_PRIMARY_MODE)
    if not ok and AHK_PRIMARY_MODE.lower() != "sendevent":
        ok = ahk_send_guess(hwnd, guess, "SendEvent")
    if not ok:
        raise RuntimeError("AHK could not send keys to the game window.")

def ahk_send_backspaces(hwnd: int, count: int, delay_s: float) -> bool:
    ahk_exe = find_ahk_exe()
    if not ahk_exe:
        return False
    delay_ms = int(round(delay_s * 1000))
    script = f"""
#Requires AutoHotkey v2.0
#SingleInstance Force
hwnd := {hwnd}
count := {count}
delay := {delay_ms}

WinActivate "ahk_id " hwnd
WinWaitActive "ahk_id " hwnd, , 2

Loop count {{
    SendEvent "{{Backspace}}"
    Sleep delay
}}
ExitApp 0
""".strip()
    script_path = Path.cwd() / "_wordle_bs.ahk"
    script_path.write_text(script, encoding="utf-8")
    try:
        p = subprocess.run([ahk_exe, str(script_path)], timeout=15)
        return p.returncode == 0
    except Exception:
        return False

def main():
    try:
        proc = psutil.Process(GAME_PID)
        print(f"[PID] {GAME_PID} exe={proc.name()}")
    except Exception:
        print("[ERROR] PID not running.")
        return

    hwnd = find_main_hwnd_by_pid(GAME_PID)
    if not hwnd:
        print("[ERROR] Could not find a visible top-level window for that PID.")
        return

    set_window_rect(hwnd, WIN_X, WIN_Y, WIN_W, WIN_H)
    time.sleep(0.2)
    activate_window(hwnd)

    all_words = load_words("wordlist.txt")
    allowed_words = all_words[:]
    print(f"[WORDS] loaded {len(all_words)}")
    print(f"[AUTO] start={START_WORD} letter_delay={LETTER_DELAY_S:.2f}s total_post_enter_wait={TOTAL_POST_ENTER_WAIT_S:.1f}s")
    print(f"[AUTO] invalid-toast check at {INVALID_TOAST_CLIENT} baseline {INVALID_BASELINE_HEX} tol {INVALID_TOL}")
    print(f"[AUTO] play-again check at {PLAY_AGAIN_CLIENT} color {PLAY_AGAIN_HEX} tol {PLAY_AGAIN_TOL}")

    with mss.mss() as sct:
        game_idx = 1
        while True:
            candidates = all_words[:]
            used = set()
            row_idx = 0
            guess = START_WORD

            print(f"\n[GAME] #{game_idx} starting")
            game_idx += 1

            while row_idx < MAX_ROWS:
                if guess in used or guess not in allowed_words:
                    nxt = pick_next_guess(candidates, allowed_words, used)
                    if not nxt:
                        print("[STOP] No guess available.")
                        break
                    guess = nxt

                used.add(guess)
                print(f"[PLAY] row {row_idx+1} guess={guess}")

                submit_guess(hwnd, guess)

                invalid = invalid_toast_triggered(hwnd, sct)
                if invalid:
                    print(f"[REJECT] {guess} not accepted by game")
                    append_reject(guess)
                    if guess in allowed_words:
                        allowed_words.remove(guess)

                    ok = ahk_send_backspaces(hwnd, BACKSPACE_COUNT, BACKSPACE_DELAY_S)
                    if not ok:
                        print("[WARN] backspace clear failed")
                    continue

                sleep_remaining_after_toast_check()

                if should_click_play_again(hwnd, sct):
                    print("[PLAY-AGAIN] detected, clicking and resetting state")
                    click_client(hwnd, PLAY_AGAIN_CLIENT[0], PLAY_AGAIN_CLIENT[1])
                    time.sleep(0.6)
                    break

                observed = read_row_feedback(hwnd, row_idx, sct)
                print(f"[FEEDBACK] {observed} (g green, y orange, b grey)")

                if observed == "ggggg":
                    print("[DONE] solved")
                    if should_click_play_again(hwnd, sct):
                        print("[PLAY-AGAIN] detected after solve, clicking")
                        click_client(hwnd, PLAY_AGAIN_CLIENT[0], PLAY_AGAIN_CLIENT[1])
                        time.sleep(0.6)
                    break

                candidates = filter_candidates(candidates, guess, observed)
                print(f"[CANDS] remaining {len(candidates)}")
                if not candidates:
                    print("[STOP] No candidates left. Possibly sampling mismatch.")
                    if should_click_play_again(hwnd, sct):
                        print("[PLAY-AGAIN] detected after stop, clicking")
                        click_client(hwnd, PLAY_AGAIN_CLIENT[0], PLAY_AGAIN_CLIENT[1])
                        time.sleep(0.6)
                    break

                nxt = pick_next_guess(candidates, allowed_words, used)
                if not nxt:
                    print("[STOP] No next guess available.")
                    break
                guess = nxt
                row_idx += 1

            if should_click_play_again(hwnd, sct):
                print("[PLAY-AGAIN] detected after final row, clicking")
                click_client(hwnd, PLAY_AGAIN_CLIENT[0], PLAY_AGAIN_CLIENT[1])
                time.sleep(0.6)

if __name__ == "__main__":
    main()
