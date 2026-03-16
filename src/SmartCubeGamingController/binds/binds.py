import abc  # Abstract Base Class
import re
import SmartCubeGamingController.binds.moves as SmartCubeMoves


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

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, SingleCharacterCommand):
            return NotImplemented
        return self.character == value.character


class KeyCombinationCommand(Command):
    def __init__(self, combination: list[SingleCharacterCommand]) -> None:
        self.combination = combination

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, KeyCombinationCommand):
            return NotImplemented
        return self.combination == value.combination


class SleepCommand(Command):
    def __init__(self, sleep_time: float) -> None:
        self.sleep_time = sleep_time

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, SleepCommand):
            return NotImplemented
        return self.sleep_time == value.sleep_time


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


class Bindings:
    def __init__(self) -> None:
        self._bindings: dict[SmartCubeMoves.MoveList, CommandList] = {}

    @property
    def bindings(self):
        return self._bindings

    def update(self, moves: SmartCubeMoves.MoveList, commands: CommandList):
        self._bindings.update({moves: commands})


def _parse_move_list(raw: str) -> SmartCubeMoves.MoveList:
    """
    Parse a whitespace-separated sequence of move tokens into a MoveList.
    Raises ValueError for unknown tokens.
    """
    from SmartCubeGamingController.binds.moves import MoveType

    token_to_move = {move.value: move for move in MoveType}
    moves: list[MoveType] = []
    for token in raw.split():
        if token not in token_to_move:
            raise ValueError(f"Unknown move token: {token!r}")
        moves.append(token_to_move[token])
    return SmartCubeMoves.MoveList().from_list(moves)


def _parse_command_token(token: str) -> Command:
    """
    Parse a single whitespace-delimited command token.

    - '1.0s', '10s'     SleepCommand
    - 'ctrl+alt+t'      KeyCombinationCommand
    - 'space', '-'      SingleCharacterCommand
    """
    sleep_regex = re.compile(r"^\d+(\.\d+)?s$")
    if sleep_regex.match(token):
        # Strip "s" from end
        bare_float = token[:-1]
        return SleepCommand(float(bare_float))
    if "+" in token:
        parts = token.split("+")
        return KeyCombinationCommand([SingleCharacterCommand(char) for char in parts])
    return SingleCharacterCommand(token)


def _parse_command_list(raw: str) -> CommandList:
    """
    Parse the right-hand side of a binding line into a KeyCommandList.
    """
    return CommandList([_parse_command_token(token) for token in raw.split()])


class BindingsConfiguration:
    """
    All possible configurations, neatly tucked away inside one class.
    """

    def __init__(self) -> None:
        self.bindings: Bindings = Bindings()
        self.deletion_type: str | None = None
        self.idle_time: float | None = None

    class DeletionType:
        Flush = "FLUSH"
        Postfix = "POSTFIX"
        Keep = "KEEP"

    def from_file(self, filepath: str):
        if ".json" in filepath:
            self._from_json(filepath)
        if ".txt" in filepath:
            self._from_txt(filepath)
        else:
            raise NotImplementedError(f"Unsupported file format.")
        return self

    def _from_json(self, filepath: str) -> None:
        raise NotImplementedError

    def _from_txt(self, filepath: str) -> None:
        # Example file:

        # ! DELETION FLUSH
        # ! IDLE_TIME 10
        # R L' - alt+tab
        # R R - ctrl+t
        # R U R' U' - ctrl+z
        # B B - shift+10.0s
        # F R - space
        # F F - ctrl+alt+t                            # terminal
        # L' U' L U - alt+space c o d e 1.0s enter    # open vscode
        # # comments

        def process_config_instruction(line: str):
            # Remove leading "!"
            body = line[1:].strip()
            parts = body.split()

            if not parts:
                return

            # Directive type should be the first token
            directive = parts[0].upper()

            if directive == "DELETION" and len(parts) >= 2:
                self.deletion_type = parts[1].upper()
            elif directive == "IDLE_TIME" and len(parts) >= 2:
                try:
                    self.idle_time = float(parts[1])
                except ValueError:
                    raise ValueError(f"Invalid IDLE_TIME value: {parts[1]!r}")
            else:
                raise ValueError(f"Unknown config directive: {body!r}")

        def process_binding_instruction(line: str):
            separator = " - "
            idx = line.find(separator)
            if idx == -1:
                raise ValueError(
                    f"Binding line missing '{separator}' separator: {line!r}"
                )
            moves_raw = line[:idx].strip()
            commands_raw = line[idx + len(separator) :].strip()
            self.bindings.update(
                _parse_move_list(moves_raw),
                _parse_command_list(commands_raw),
            )

        with open(filepath) as file:
            for raw_line in file.readlines():
                line = raw_line.strip()

                # Handle comments
                if not line or line.startswith("#"):
                    continue
                comment_idx = line.find(" #")
                if comment_idx != -1:
                    line = line[:comment_idx].strip()

                if line.startswith("!"):
                    process_config_instruction(line)
                else:
                    process_binding_instruction(line)
