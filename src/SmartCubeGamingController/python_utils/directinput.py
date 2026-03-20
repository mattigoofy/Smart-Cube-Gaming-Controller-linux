"""Linux (Wayland/X) implementation using python-evdev and uinput.

Requires: pip install evdev
Requires access to /dev/uinput (run as root or add a udev rule).
"""

# TODO refactor and move this file
import platform
import subprocess
import time

import pyautogui
import pyperclip
from evdev import UInput
from evdev import ecodes as e

# Build a CHAR_MAP mapping similar to the previous Windows layout.
CHAR_MAP = {}
for c in "abcdefghijklmnopqrstuvwxyz":
    CHAR_MAP[c] = getattr(e, "KEY_" + c.upper())

# digits
CHAR_MAP.update(
    {
        "1": e.KEY_1,
        "2": e.KEY_2,
        "3": e.KEY_3,
        "4": e.KEY_4,
        "5": e.KEY_5,
        "6": e.KEY_6,
        "7": e.KEY_7,
        "8": e.KEY_8,
        "9": e.KEY_9,
        "0": e.KEY_0,
        ",": e.KEY_COMMA,
        ";": e.KEY_SEMICOLON,
        ":": e.KEY_SEMICOLON,
        "=": e.KEY_EQUAL,
    }
)

# common keys
CHAR_MAP["space"] = e.KEY_SPACE
CHAR_MAP["enter"] = e.KEY_ENTER
CHAR_MAP["return"] = e.KEY_ENTER
CHAR_MAP["tab"] = e.KEY_TAB
CHAR_MAP["backspace"] = e.KEY_BACKSPACE

# arrow keys
CHAR_MAP["left arrow"] = e.KEY_LEFT
CHAR_MAP["right arrow"] = e.KEY_RIGHT
CHAR_MAP["up arrow"] = e.KEY_UP
CHAR_MAP["down arrow"] = e.KEY_DOWN

# modifiers and a few extras
CHAR_MAP["shift"] = e.KEY_LEFTSHIFT
CHAR_MAP["ctrl"] = e.KEY_LEFTCTRL
CHAR_MAP["alt"] = e.KEY_LEFTALT


UNPRINTABLE_KEYS = [
    "space",
    "enter",
    "return",
    "tab",
    "backspace",
    "left arrow",
    "right arrow",
    "up arrow",
    "down arrow",
    "shift",
    "ctrl",
    "alt",
]

# Create a UInput device. On some systems providing capabilities is required,
# but the default should work for most cases.
ui = UInput()


def press_key(key):
    ui.write(e.EV_KEY, key, 1)
    ui.syn()


def release_key(key):
    ui.write(e.EV_KEY, key, 0)
    ui.syn()


def execute_combo(keys_list):
    for combo in keys_list:
        # Shell command
        if combo[0] == "__shell__":
            subprocess.Popen(combo[1], shell=True)
            continue

        # Delay step: e.g. ['1.0s']
        if len(combo) == 1 and combo[0].endswith("s"):
            try:
                time.sleep(float(combo[0][:-1]))
                continue
            except ValueError:
                pass

        # Single characters
        if (len(combo) == 1) and combo not in list(CHAR_MAP.keys()):
            if combo[0] not in UNPRINTABLE_KEYS:
                write_unicode_string(combo[0])
            else:
                press_key(CHAR_MAP[combo[0]])
                release_key(CHAR_MAP[combo[0]])
            # Don't execute the rest of this code; short-circuits
            return

        # Key combo: press all together, then release
        keys = [CHAR_MAP[k] for k in combo if k in CHAR_MAP]
        for k in keys:
            press_key(k)
        time.sleep(0.05)
        for k in reversed(keys):
            release_key(k)


def write_unicode_string(text: str):
    pyperclip.copy(text)
    if platform.system() == "Darwin":
        pyautogui.hotkey("command", "v")
    else:
        press_key(CHAR_MAP["ctrl"])
        press_key(CHAR_MAP["v"])
        release_key(CHAR_MAP["ctrl"])
        release_key(CHAR_MAP["v"])
   