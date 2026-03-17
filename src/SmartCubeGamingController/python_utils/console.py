import enum

from SmartCubeGamingController.binds.moves import MoveType
from SmartCubeGamingController.python_utils.directinput import CHAR_MAP, press_key, release_key


class Directions(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    RIGHT = enum.auto()
    LEFT = enum.auto()


# TODO This file may not be the place for this class. Move it to where the console mode handler is (or will be)
class CursorState:
    row: int
    column: int
    shift_lock: bool

    def __init__(self, row: int, column: int, shift_lock: bool):
        self.row = row
        self.column = column
        self.shift_lock = shift_lock

    def to_dict(self):
        return {
            "row": self.row,
            "col": self.column,
            "shiftlock": self.shift_lock,
        }


class Keyboard:
    AZERTY = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["a", "z", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["q", "s", "d", "f", "g", "h", "j", "k", "l", "m"],
        ["w", "x", "c", "v", "b", "n", ",", ";", ":", "="],
    ]

    QWERTY = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";"],
        ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
    ]

    cursor = CursorState(1, 0, False)

    def __init__(self):
        self.KEYBOARD = self.AZERTY

    def move_cursor(self, direction: Directions):
        if direction == Directions.UP:
            self.cursor.row -= 1
        if direction == Directions.DOWN:
            self.cursor.row += 1
        if direction == Directions.RIGHT:
            self.cursor.column += 1
        if direction == Directions.LEFT:
            self.cursor.column -= 1

        self.cursor.row %= len(self.KEYBOARD)
        self.cursor.column %= len(self.KEYBOARD[self.cursor.row])

    def current_key(self):
        return CHAR_MAP[self.KEYBOARD[self.cursor.row][self.cursor.column]]

    def press_key(self, key):
        if self.cursor.shift_lock:
            press_key(CHAR_MAP["shift"])
            press_key(key)
            release_key(CHAR_MAP["shift"])
            release_key(key)
        else:
            press_key(key)
            release_key(key)

    def press_cursor(self):
        key = self.current_key()
        if self.cursor.shift_lock:
            press_key(CHAR_MAP["shift"])
            press_key(key)
            release_key(CHAR_MAP["shift"])
            release_key(key)
        else:
            press_key(key)
            release_key(key)


class Console:
    def __init__(self):
        self.keyboard = Keyboard()

    def handle_move(self, move: MoveType):
        if move == MoveType.R:
            self.keyboard.move_cursor(Directions.UP)

        if move == MoveType.R_PRIME:
            self.keyboard.move_cursor(Directions.DOWN)

        if move == MoveType.U:
            self.keyboard.move_cursor(Directions.RIGHT)

        if move == MoveType.U_PRIME:
            self.keyboard.move_cursor(Directions.LEFT)

        if move == MoveType.L:
            self.keyboard.press_cursor()

        if move == MoveType.L_PRIME:
            key = CHAR_MAP["backspace"]
            self.keyboard.press_key(key)

        if move == MoveType.D:
            key = CHAR_MAP["space"]
            self.keyboard.press_key(key)

        if move == MoveType.D_PRIME:
            self.keyboard.cursor.shift_lock = not self.keyboard.cursor.shift_lock

        if move == MoveType.F:
            key = CHAR_MAP["right arrow"]
            self.keyboard.press_key(key)

        if move == MoveType.F_PRIME:
            key = CHAR_MAP["left arrow"]
            self.keyboard.press_key(key)

        if move == MoveType.B:
            key = CHAR_MAP["up arrow"]
            self.keyboard.press_key(key)

        if move == MoveType.B_PRIME:
            key = CHAR_MAP["down arrow"]
            self.keyboard.press_key(key)
