"""Linux (Wayland/X) implementation using python-evdev and uinput.

Requires: pip install evdev
Requires access to /dev/uinput (run as root or add a udev rule).
"""

from evdev import UInput
from evdev import ecodes


# UNPRINTABLE_KEYS = [
#     "space",
#     "enter",
#     "return",
#     "tab",
#     "backspace",
#     "left arrow",
#     "right arrow",
#     "up arrow",
#     "down arrow",
#     "shift",
#     "ctrl",
#     "alt",
# ]


class KeyboardMap:
    def __init__(self) -> None:
        self._character_map: dict[str, int] = self.default_map()

        # Create a UInput device. On some systems providing capabilities is required,
        # but the default should work for most cases.
        self._input = UInput()

    def default_map(self) -> dict[str, int]:
        map: dict[str, int] = dict()

        # Map in the form of { "a": <key as int> }
        for c in "abcdefghijklmnopqrstuvwxyz":
            map[c] = getattr(ecodes, "KEY_" + c.upper())

        # Digits
        map.update(
            {
                "1": ecodes.KEY_1,
                "2": ecodes.KEY_2,
                "3": ecodes.KEY_3,
                "4": ecodes.KEY_4,
                "5": ecodes.KEY_5,
                "6": ecodes.KEY_6,
                "7": ecodes.KEY_7,
                "8": ecodes.KEY_8,
                "9": ecodes.KEY_9,
                "0": ecodes.KEY_0,
                ",": ecodes.KEY_COMMA,
                ";": ecodes.KEY_SEMICOLON,
                ":": ecodes.KEY_SLASH,  # NOTE there does not seem to be a key code for ":" (https://pickpj.github.io/keycodes.html)
                "=": ecodes.KEY_EQUAL,
            }
        )

        # Common keys
        map["space"] = ecodes.KEY_SPACE
        map["enter"] = ecodes.KEY_ENTER
        map["return"] = ecodes.KEY_ENTER
        map["tab"] = ecodes.KEY_TAB
        map["backspace"] = ecodes.KEY_BACKSPACE

        # Arrow keys
        map["left arrow"] = ecodes.KEY_LEFT
        map["right arrow"] = ecodes.KEY_RIGHT
        map["up arrow"] = ecodes.KEY_UP
        map["down arrow"] = ecodes.KEY_DOWN

        # Modifiers and a few extras
        map["shift"] = ecodes.KEY_LEFTSHIFT
        map["ctrl"] = ecodes.KEY_LEFTCTRL
        map["alt"] = ecodes.KEY_LEFTALT

        return map
    
    def press_key(self, key: str):
        """
        Press a key.

        Args:
            key (str): Key to press, in string form. Example: "left arrow", "a", "ctrl" and so on.
        """
        # https://python-evdev.readthedocs.io/en/latest/apidoc.html#evdev.eventio.EventIO.write
        # The evdev module doesn't play well with pylance, so no autocomplete here
        key_code = self.get(key)
        self._input.write(ecodes.EV_KEY, key_code, 1)
        self._input.syn()


    def release_key(self, key: str):
        """
        Release a key.

        Args:
            key (str): Key to press, in string form. Example: "left arrow", "a", "ctrl" and so on.
        """
        key_code = self.get(key)
        self._input.write(ecodes.EV_KEY, key_code, 0)
        self._input.syn()

    def get(self, key: str) -> int:
        mapped = self._character_map.get(key)
        if not mapped:
            raise ValueError(f"Key not found: {key}")
        return mapped
    