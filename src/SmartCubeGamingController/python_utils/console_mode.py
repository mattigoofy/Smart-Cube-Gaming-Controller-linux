import queue
import threading

from .directinput import CHAR_MAP, press_key, release_key
from .server import cursor_state, move_queue

KEYBOARD = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["a", "z", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["q", "s", "d", "f", "g", "h", "j", "k", "l", "m"],
    ["w", "x", "c", "v", "b", "n", ",", ";", ":", "="],
]


def _push_cursor(row: int, col: int, shiftlock: bool) -> None:
    cursor_state["row"] = row
    cursor_state["col"] = col
    cursor_state["shiftlock"] = shiftlock


def run_console_mode(stop_event: threading.Event):
    shiftlock = False
    idx = [1, 0]  # [row, column]
    _push_cursor(idx[0], idx[1], shiftlock)

    while not stop_event.is_set():
        try:
            move = move_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        try:
            if "R" in move:  # move row up or down
                idx[0] += -1 if "'" in move else 1
                idx[0] %= sum(1 for row in KEYBOARD if idx[1] < len(row))

            if "U" in move:  # move column left or right
                idx[1] += -1 if "'" in move else 1
                idx[1] %= len(KEYBOARD[idx[0]])

            if "L" in move:  # write or delete
                if "'" in move:
                    key = CHAR_MAP["backspace"]
                    press_key(key)
                    release_key(key)
                else:
                    if shiftlock:
                        press_key(CHAR_MAP["shift"])
                        press_key(CHAR_MAP[KEYBOARD[idx[0]][idx[1]]])
                        release_key(CHAR_MAP["shift"])
                        release_key(CHAR_MAP[KEYBOARD[idx[0]][idx[1]]])
                    else:
                        key = CHAR_MAP[KEYBOARD[idx[0]][idx[1]]]
                        press_key(key)
                        release_key(key)

            if "D" in move:  # space or toggle shiftlock
                if "'" in move:
                    key = CHAR_MAP["space"]
                    press_key(key)
                    release_key(key)
                else:
                    shiftlock = not shiftlock

            if "F" in move:  # arrow left or right
                key = CHAR_MAP["left arrow"] if "'" in move else CHAR_MAP["right arrow"]
                press_key(key)
                release_key(key)

            if "B" in move:  # arrow up or down
                key = CHAR_MAP["up arrow"] if "'" in move else CHAR_MAP["down arrow"]
                press_key(key)
                release_key(key)

            _push_cursor(idx[0], idx[1], shiftlock)
            print("letter:", KEYBOARD[idx[0]][idx[1]])
        except Exception as ex:
            print("ERROR:", ex)
