import abc # Abstract Base Class

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # Use these imports only when type checking. This resolves a circular import issue when trying to run.
    from SmartCubeGamingController.binds.moves import MoveList


class Command(abc.ABC):
    """
    Abstract base class of a Command for use in a `KeyCommandList`
    """
    # NOTE functions applicable to all Commands can be defined here, and will be inherited.
    def execute(self) -> None:
        """
        Execute this command. This could be typing a key combination, or waiting a certain amount of time. This method needs to be overwritten in inheriting classes.
        """
        raise NotImplementedError(f"Execute not implemented for {type(self)}")


class SingleCharacterCommand(Command):
    def __init__(self, character: str) -> None:
        self.character = character

    def is_on_keyboard(self) -> bool:
        """
        True if this key is a valid key on a keyboard (for example, "a", "win", "left arrow", or "ctrl"), False otherwise (for example, "A", or "😭")
        """
        raise NotImplementedError


class KeyCombinationCommand(Command):
    def __init__(self, combination: list[SingleCharacterCommand]) -> None:
        self.combination = combination


class SleepCommand(Command):
    def __init__(self, sleep_time: int) -> None:
        self.sleep_time = sleep_time


class KeyCommandList():
    """
    A list of commands to be executed. A command can be a single character, a key combination, or a sleep command.
    """
    def __init__(self, commands: list[Command]) -> None:
        self.commands = commands


class Bindings():
    def __init__(self) -> None:
        self._bindings: dict[MoveList, KeyCommandList] = {}

    @property
    def bindings(self):
        return self._bindings

    def update(self, moves: MoveList, commands: KeyCommandList):
        self._bindings.update({ moves: commands })


class BindingsConfiguration():
    """
    All possible configurations, neatly tucked away inside one class.
    """
    def __init__(self) -> None:
        self.bindings: Bindings
        # NOTE other settings like deletion_type (flush, postfix, keep) and time_idle (time after which the buffer gets cleared due to inactivity), can be defined here.

    def from_file(self, filepath: str) -> None:
        if ".json" in filepath:
            self._from_json(filepath)
            return None
        if ".txt" in filepath:
            self._from_txt(filepath)
            return None
        raise NotImplementedError(f"Unsupported file format.")

    def _from_json(self, filepath: str) -> None:
        raise NotImplementedError
    
    def _from_txt(self, filepath: str) -> None:
        raise NotImplementedError
