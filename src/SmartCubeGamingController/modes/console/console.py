import enum

from SmartCubeGamingController.modes.binds.moves import MoveType
from SmartCubeGamingController.modes.directinput import KeyboardMap


class Directions(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    RIGHT = enum.auto()
    LEFT = enum.auto()


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
        self._keyboard = self.AZERTY
        self._keyboard_map = KeyboardMap()

    @property
    def map(self):
        return self._keyboard_map

    def move_cursor(self, direction: Directions):
        if direction == Directions.UP:
            self.cursor.row -= 1
        if direction == Directions.DOWN:
            self.cursor.row += 1
        if direction == Directions.RIGHT:
            self.cursor.column += 1
        if direction == Directions.LEFT:
            self.cursor.column -= 1

        self.cursor.row %= len(self._keyboard)
        self.cursor.column %= len(self._keyboard[self.cursor.row])

    def current_key(self):
        return self._keyboard[self.cursor.row][self.cursor.column]

    def press_key(self, key: str):
        if self.cursor.shift_lock:
            self.map.press_key("shift")
            self.map.press_key(key)
            self.map.release_key("shift")
            self.map.release_key(key)
        else:
            self.map.press_key(key)
            self.map.release_key(key)

    def press_cursor(self):
        key = self.current_key()
        self.press_key(key)


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
            self.keyboard.press_key("backspace")

        if move == MoveType.D:
            self.keyboard.press_key("space")

        if move == MoveType.D_PRIME:
            self.keyboard.cursor.shift_lock = not self.keyboard.cursor.shift_lock

        if move == MoveType.F:
            self.keyboard.press_key("right arrow")

        if move == MoveType.F_PRIME:
            self.keyboard.press_key("left arrow")

        if move == MoveType.B:
            self.keyboard.press_key("up arrow")

        if move == MoveType.B_PRIME:
            self.keyboard.press_key("down arrow")
