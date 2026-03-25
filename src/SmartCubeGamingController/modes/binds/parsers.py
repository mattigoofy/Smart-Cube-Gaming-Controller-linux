import abc
from dataclasses import dataclass
import enum
import re

import SmartCubeGamingController.modes.binds.moves as SmartCubeMoves
import SmartCubeGamingController.modes.binds.binds as SmartCubeBinds


def _parse_move_list(raw: str) -> "SmartCubeMoves.MoveList":
    """
    Parse a whitespace-separated sequence of move tokens into a MoveList, for example "U R' B D".
    Raises ValueError for unknown tokens.
    """
    from SmartCubeGamingController.modes.binds.moves import MoveType

    moves: list[MoveType] = []
    for token in raw.split():
        moves.append(MoveType(token))
    return SmartCubeMoves.MoveList().from_list(moves)


def _parse_command_token(token: str) -> "SmartCubeBinds.Command":
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
        return SmartCubeBinds.SleepCommand(float(bare_float))
    if "+" in token:
        parts = token.split("+")
        return SmartCubeBinds.KeyCombinationCommand(
            [SmartCubeBinds.KeyCommand(char) for char in parts]
        )
    return SmartCubeBinds.KeyCommand(token)


def _parse_command_list(raw: str) -> "SmartCubeBinds.CommandList":
    """
    Parse the right-hand side of a binding line into a KeyCommandList.
    """
    return SmartCubeBinds.CommandList(
        [_parse_command_token(token) for token in raw.split()]
    )


class FileExtension(enum.Enum):
    TXT = "txt"
    JSON = "json"
    YAML = "yml"

    @staticmethod
    def from_str(filepath: str):
        if filepath[-3:].lower() in ("txt"):
            return FileExtension.TXT
        if filepath[-4:].lower() in ("json"):
            return FileExtension.JSON
        if filepath[-3:].lower() in ("yml") or filepath[-4:].lower() in ("yaml"):
            return FileExtension.YAML

        raise NotImplementedError


class Parser(abc.ABC):
    @abc.abstractmethod
    def parse(self, filepath: str) -> "SmartCubeBinds.BindingsConfiguration":
        ...

    @abc.abstractmethod
    def export(self, config: "SmartCubeBinds.BindingsConfiguration", filepath: str) -> None:
        ...

    @classmethod
    def for_file(cls, filepath: str) -> "Parser":
        match FileExtension.from_str(filepath):
            case FileExtension.TXT:
                return TxtParser()
            case FileExtension.JSON:
                return JsonParser()
            case FileExtension.YAML:
                return YamlParser()
            
    @classmethod
    def parse_file(cls, filepath: str) -> "SmartCubeBinds.BindingsConfiguration":
        return cls.for_file(filepath).parse(filepath)

    @classmethod
    def export_file(cls, config: "SmartCubeBinds.BindingsConfiguration", filepath: str) -> None:
        cls.for_file(filepath).export(config, filepath)


class TxtParser(Parser):
    def parse(self, filepath: str) -> "SmartCubeBinds.BindingsConfiguration":
        # TODO shell commands

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

        result = SmartCubeBinds.BindingsConfiguration()

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
                    partial_config = self._process_config_instruction(line)
                    if not partial_config:
                        continue

                    # Update result
                    if partial_config.deletion_type:
                        result.deletion_type = partial_config.deletion_type
                    if partial_config.idle_time:
                        result.idle_time = partial_config.idle_time
                else:
                    partial_binding = self._process_binding_instruction(line)
                    if not partial_binding:
                        continue

                    # Update result
                    result.bindings.extend(partial_binding)

        return result
    
    def export(self, config: "SmartCubeBinds.BindingsConfiguration", filepath: str) -> None:
        ...

    @dataclass
    class DirectiveConfig:
        deletion_type: "SmartCubeBinds.BindingsConfiguration.DeletionType | None" = None
        idle_time: float | None = None

    def _process_config_instruction(self, line: str) -> DirectiveConfig | None:
        deletion_type: "SmartCubeBinds.BindingsConfiguration.DeletionType | None" = None
        idle_time: float | None = None

        # Remove leading "!"
        body = line[1:].strip()
        parts = body.split()

        if not parts:
            return

        # Directive type should be the first token
        directive = parts[0].lower()

        if directive == "deletion" and len(parts) >= 2:
            deletion_type = SmartCubeBinds.BindingsConfiguration.DeletionType(
                parts[1].lower()
            )
        elif directive == "idle_time" and len(parts) >= 2:
            try:
                idle_time = float(parts[1])
            except ValueError:
                raise ValueError(f"Invalid IDLE_TIME value: {parts[1]!r}")
        else:
            raise ValueError(f"Unknown config directive: {body!r}")

        return self.DirectiveConfig(deletion_type, idle_time)

    def _process_binding_instruction(self, line: str) -> "SmartCubeBinds.Bindings":
        separator = " - "
        idx = line.find(separator)
        if idx == -1:
            raise ValueError(f"Binding line missing '{separator}' separator: {line!r}")
        moves_raw = line[:idx].strip()
        commands_raw = line[idx + len(separator) :].strip()

        return SmartCubeBinds.Bindings().update(
            _parse_move_list(moves_raw),
            _parse_command_list(commands_raw),
        )


class JsonParser(Parser):
    def parse(self, filepath: str) -> "SmartCubeBinds.BindingsConfiguration":
        raise NotImplementedError

    #     # Example file

    #     # [
    #     #     {
    #     #         "type": "Command",
    #     #         "name": "DELETION",
    #     #         "value": "FLUSH"
    #     #     },
    #     #     {
    #     #         "type": "bind",
    #     #         "formula": "R U R' U'",
    #     #         "keys": "ctrl+z"
    #     #     },
    #     #     {
    #     #         "type": "shell",
    #     #         "formula": "F F",
    #     #         "command": "ls ~"
    #     #     }
    #     # ]

    #     class TypeJSON(enum.Enum):
    #         """
    #         An abstraction of a types in the json file
    #         """

    #         COMMAND = "command"
    #         BIND = "bind"
    #         SHELL = "shell"

    #         @staticmethod
    #         def from_str(label: str):
    #             if label.lower() in ("command", "config", "commands"):
    #                 return TypeJSON.COMMAND
    #             if label.lower() in ("bind", "binding"):
    #                 return TypeJSON.BIND
    #             if label.lower() in ("shell"):
    #                 return TypeJSON.SHELL

    #     def process_command_instruction(entry: str):
    #         self.deletion_type = entry["name"].upper()
    #         self.idle_time = float(entry["value"])

    #     def process_binding_instruction(entry: str):
    #         moves = entry["formula"].upper().strip()
    #         keys = entry["keys"].upper().strip()
    #         self.bindings.update(
    #             _parse_move_list(moves),
    #             _parse_command_list(keys),
    #         )

    #     def process_shell_instruction(entry: str):
    #         raise NotImplementedError

    #     with open(filepath) as file:
    #         for entry in json.load(file):
    #             type = entry["type"].lower()

    #             label = TypeJSON.from_str(type)

    #             if label == TypeJSON.COMMAND:
    #                 process_command_instruction(entry)
    #             elif label == TypeJSON.BIND:
    #                 process_binding_instruction(entry)
    #             elif label == TypeJSON.SHELL:
    #                 process_shell_instruction(entry)
    #             else:
    #                 raise Exception("Invalid JSON type")

    def export(self, config: "SmartCubeBinds.BindingsConfiguration", filepath: str) -> None:
        ...


class YamlParser(Parser):
    class CommandKeys(enum.Enum):
        TEXT = "text"
        KEYS = "keys"
        SHELL = "shell"
        COMBO = "combo"
        SLEEP = "sleep"

        @staticmethod
        def from_str(value: str):
            try:
                return YamlParser.CommandKeys(value)
            except ValueError:
                return None

    def parse(self, filepath: str) -> "SmartCubeBinds.BindingsConfiguration":
        """Example file

        deletion_type: flush
        idle_time: 10.0s
        bindings:
        - moves: U R U' R'
            command_list:
            - text: abc def
            - keys: enter
            - shell: ls ~
            - combo: shift a
            - sleep: 5s
        """
        import yaml

        with open(filepath) as file:
            yml_dict = yaml.safe_load(file)

        config = SmartCubeBinds.BindingsConfiguration()

        # TODO defaults, instead of assuming these directives are always defined
        config.deletion_type = SmartCubeBinds.BindingsConfiguration.DeletionType(
            yml_dict["deletion_type"]
        )
        config.idle_time = float(yml_dict["idle_time"][:-1])  # remove 's'

        for item in yml_dict["bindings"]:
            moves_list: list[SmartCubeMoves.MoveType] = []
            command_list: list[SmartCubeBinds.Command] = []

            moves = item["moves"].split()
            for move in moves:
                moves_list.append(SmartCubeMoves.MoveType(move))

            for command in item["commands"]:
                command_key = list(command.keys())[0]
                command_value = list(command.values())[0]
                key = YamlParser.CommandKeys(command_key)

                command_list.append(self._command_key_to_command(key, command_value))

            config.bindings.update(
                SmartCubeMoves.MoveList().from_list(moves_list),
                SmartCubeBinds.CommandList(command_list),
            )

        return config
    
    def export(self, config: "SmartCubeBinds.BindingsConfiguration", filepath: str) -> None:
        import yaml

        yml_dict = {
            "deletion_type": config.deletion_type.value,
            "idle_time": f"{config.idle_time}s",
            "bindings": []
        }

        for move_list, command_list in config.bindings.bindings.items():
            commands: list[dict] = []
            for command in command_list:
                commands.append(self._command_to_dict(command))

            yml_dict["bindings"].append({
                "moves": " ".join(move.value for move in move_list),
                "commands": commands
            })

        with open(filepath, mode="w") as f:
            yaml.safe_dump(yml_dict, f, default_flow_style=False)

    def _command_key_to_command(
        self, command_key: CommandKeys, value: str
    ) -> "SmartCubeBinds.Command":
        match command_key:
            case YamlParser.CommandKeys.TEXT:
                return SmartCubeBinds.TextCommand(value)
            case YamlParser.CommandKeys.KEYS:
                return SmartCubeBinds.KeyCommand(value)
            case YamlParser.CommandKeys.SHELL:
                return SmartCubeBinds.ShellCommand(value)
            case YamlParser.CommandKeys.COMBO:
                combo_list: list[SmartCubeBinds.KeyCommand] = []
                for combo_key in value.split():
                    combo_list.append(SmartCubeBinds.KeyCommand(combo_key))
                return SmartCubeBinds.KeyCombinationCommand(combo_list)
            case YamlParser.CommandKeys.SLEEP:
                return SmartCubeBinds.SleepCommand(float(value[:-1]))
        raise NotImplementedError
    
    def _command_to_dict(self, command: "SmartCubeBinds.Command") -> dict:
        match command:
            case SmartCubeBinds.TextCommand():
                return {YamlParser.CommandKeys.TEXT.value: command.text}
            case SmartCubeBinds.KeyCommand():
                return {YamlParser.CommandKeys.KEYS.value: command.key}
            case SmartCubeBinds.ShellCommand():
                return {YamlParser.CommandKeys.SHELL.value: command.shell_command}
            case SmartCubeBinds.KeyCombinationCommand():
                keys = " ".join(k.key for k in command.combination)
                return {YamlParser.CommandKeys.COMBO.value: keys}
            case SmartCubeBinds.SleepCommand():
                return {YamlParser.CommandKeys.SLEEP.value: f"{command.duration}s"}
            case _:
                raise NotImplementedError
