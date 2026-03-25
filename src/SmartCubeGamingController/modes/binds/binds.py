import abc  # Abstract Base Class
import enum
import subprocess
import time

import pyperclip
from evdev import UInput
from evdev import ecodes as e

import SmartCubeGamingController.modes.binds.moves as SmartCubeMoves
import SmartCubeGamingController.modes.binds.parsers as SmartCubeParsers
from SmartCubeGamingController.modes.directinput import CHAR_MAP


class Command(abc.ABC):
    """
    Abstract base class of a Command for use in a `KeyCommandList`
    """

    # NOTE functions applicable to all Commands can be defined here, and will be inherited.
    @abc.abstractmethod
    def execute(self) -> None:
        """
        Execute this command. This could be typing a key combination, or waiting a certain amount of time. This method needs to be overwritten in inheriting classes.
        """
        ...


class TextCommand(Command):
    """
    Types arbitrary unicode text by pasting it with ctrl+v.
    """

    def __init__(self, text: str) -> None:
        self.text = text

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, TextCommand):
            return NotImplemented
        return self.text == obj.text

    def _is_on_keyboard(self) -> bool:
        """
        True if this key is a valid key on a keyboard (for example, "a", "win", "left arrow", or "ctrl"), False otherwise (for example, "A", or "😭")
        """
        raise NotImplementedError

    def execute(self) -> None:
        # TODO Check if self.text exists as a single character on keyboard. If so, execute as KeyCommand instead.
        pyperclip.copy(self.text)
        # ctrl+v
        ctrl = KeyCommand("ctrl")
        v = KeyCommand("v")
        ctrl.press()
        v.press()
        ctrl.release()
        v.release()


class KeyCommand(Command):
    """
    A command that presses a key on keyboard. This needs to be an actual press-able key on your keyboard, so _characters_ like "A" won't work. Please use a TextCommand or KeyCombinationCommand instead for those cases.
    """

    def __init__(self, key: str) -> None:
        self.key = key
        self.ui = UInput()

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, KeyCommand):
            return NotImplemented
        return self.key == value.key

    def execute(self) -> None:
        self.press()
        self.release()

    # TODO Use press and release from directinput.py instead
    def press(self) -> None:
        self.ui.write(e.EV_KEY, CHAR_MAP[self.key], 1)
        self.ui.syn()

    def release(self) -> None:
        self.ui.write(e.EV_KEY, CHAR_MAP[self.key], 0)
        self.ui.syn()


class KeyCombinationCommand(Command):
    """
    A command that executes a key combination by pressing multiple keys at once.
    """

    def __init__(self, combination: list[KeyCommand]) -> None:
        self.combination = combination

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, KeyCombinationCommand):
            return NotImplemented
        return self.combination == obj.combination

    def execute(self) -> None:
        # first press all keys
        for key in self.combination:
            key.press()

        # the releases all keys
        for key in self.combination:
            key.release()


class SleepCommand(Command):
    """
    A command that sleeps for a given amount of time.
    """

    def __init__(self, sleep_time: float) -> None:
        self.sleep_time = sleep_time

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, SleepCommand):
            return NotImplemented
        return self.sleep_time == obj.sleep_time

    def execute(self) -> None:
        time.sleep(self.sleep_time)


class ShellCommand(Command):
    """
    A command that executes a shell instruction.
    """

    def __init__(self, shell_command: str) -> None:
        self.shell_command = shell_command

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, ShellCommand):
            return NotImplemented
        return self.shell_command == obj.shell_command

    def execute(self) -> None:
        subprocess.Popen(self.shell_command, shell=True)


class CommandList:
    """
    A list of commands to be executed. A command can be a single character, a key combination, or a sleep command.
    """

    def __init__(self, commands: list[Command]) -> None:
        self.commands = commands

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CommandList):
            return NotImplemented
        return self.commands == other.commands
    
    def __iter__(self):
        return iter(self.commands)

    def execute(self):
        for cmd in self.commands:
            cmd.execute()


class Bindings:
    def __init__(self) -> None:
        self._bindings: dict["SmartCubeMoves.MoveList", CommandList] = {}

    @property
    def bindings(self):
        return self._bindings

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bindings):
            return NotImplemented
        return self._bindings == other._bindings

    def update(self, moves: "SmartCubeMoves.MoveList", commands: CommandList):
        self._bindings.update({moves: commands})
        return self
    
    def extend(self, bindings: "Bindings"):
        for move_list, command_list in bindings.bindings.items():
            self.update(move_list, command_list)


# TODO Add ability to export (as yaml, as json, as txt)
class BindingsConfiguration:
    """
    All possible configurations, neatly tucked away inside one class.
    """

    def __init__(self) -> None:
        self.bindings: Bindings = Bindings()
        self.deletion_type: BindingsConfiguration.DeletionType = (
            BindingsConfiguration.DeletionType.Flush
        )
        self.idle_time: float = 10.0

    class DeletionType(enum.Enum):
        Flush = "flush"
        Postfix = "postfix"
        Keep = "keep"

        @staticmethod
        def from_str(value: str):
            try:
                return BindingsConfiguration.DeletionType(value.upper())
            except ValueError:
                return None

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, BindingsConfiguration):
            return NotImplemented
        return (
            self.bindings == obj.bindings
            and self.deletion_type == obj.deletion_type
            and self.idle_time == obj.idle_time
        )

    def from_file(self, filepath: str):
        self = SmartCubeParsers.Parser.parse_file(filepath)
        return self
    
    def export(self, filepath: str):
        SmartCubeParsers.Parser.export_file(self, filepath)
