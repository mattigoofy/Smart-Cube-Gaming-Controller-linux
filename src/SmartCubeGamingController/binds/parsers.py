from dataclasses import dataclass
import enum
import re

import SmartCubeGamingController.binds.moves as SmartCubeMoves
import SmartCubeGamingController.binds.binds as SmartCubeBinds


def _parse_move_list(raw: str) -> "SmartCubeMoves.MoveList":
    """
    Parse a whitespace-separated sequence of move tokens into a MoveList, for example "U R' B D".
    Raises ValueError for unknown tokens.
    """
    from SmartCubeGamingController.binds.moves import MoveType

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
        return SmartCubeBinds.KeyCombinationCommand([SmartCubeBinds.KeyCommand(char) for char in parts])
    return SmartCubeBinds.KeyCommand(token)


def _parse_command_list(raw: str) -> "SmartCubeBinds.CommandList":
    """
    Parse the right-hand side of a binding line into a KeyCommandList.
    """
    return SmartCubeBinds.CommandList([_parse_command_token(token) for token in raw.split()])

import SmartCubeGamingController.binds.moves as SmartCubeMoves


class FileExtensions(enum.Enum):
    TXT = "txt"
    JSON = "json"
    YAML = "yml"

    @staticmethod
    def from_str(filepath: str):
        if filepath[-3:].lower() in ("txt"):
            return FileExtensions.TXT
        if filepath[-4:].lower() in ("json"):
            return FileExtensions.JSON
        if filepath[-3:].lower() in ("yml") or filepath[-4:].lower() in ("yaml"):
            return FileExtensions.YAML
        
        raise NotImplemented


class CommandKeys(enum.Enum):
    TEXT = "text"
    KEYS = "keys"
    SHELL = "shell"
    COMBO = "combo"
    SLEEP = "sleep"

    @staticmethod
    def from_str(value: str):
        try:
            return CommandKeys(value)
        except ValueError:
            return None


class Parser:
    def parse(self, file_path: str) -> "SmartCubeBinds.BindingsConfiguration":
        extension = FileExtensions.from_str(file_path)
        parser = None
        
        if extension == FileExtensions.TXT:
            parser = TxtParser()
        if extension == FileExtensions.JSON:
            parser = JsonParser()
        if extension == FileExtensions.YAML:
            parser = YamlParser()
            
        if not parser:
            raise ValueError("No valid file extension found.")
        
        return parser.parse(file_path)


class TxtParser(Parser):
    def parse(self, file_path: str) -> "SmartCubeBinds.BindingsConfiguration":
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

        with open(file_path) as file:
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
            deletion_type = SmartCubeBinds.BindingsConfiguration.DeletionType(parts[1].lower())
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
            raise ValueError(
                f"Binding line missing '{separator}' separator: {line!r}"
            )
        moves_raw = line[:idx].strip()
        commands_raw = line[idx + len(separator) :].strip()

        return SmartCubeBinds.Bindings().update(
            _parse_move_list(moves_raw),
            _parse_command_list(commands_raw),
        )


class JsonParser(Parser):
    def parse(self, file_path: str) -> "SmartCubeBinds.BindingsConfiguration":
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


class YamlParser(Parser):
    def parse(self, file_path: str) -> "SmartCubeBinds.BindingsConfiguration":
        """Example file

        deletion_type: flush
        idle_time: 10.0s
        bindings:
        - moves: U R U' R'
            commands:
            - text: abc def
            - keys: enter
            - shell: ls ~
            - combo: shift a
            - sleep: 5s
        """
        import yaml

        from SmartCubeGamingController.binds.moves import MoveType

        with open(file_path) as file:
            yml_dict = yaml.safe_load(file)

        config = SmartCubeBinds.BindingsConfiguration()
        config.deletion_type = yml_dict["deletion_type"]
        config.idle_time = float(yml_dict["idle_time"][:-1])  # remove 's'
        moves: list[MoveType] = []
        for item in yml_dict["bindings"]:
            moves.append(item["moves"])

        commands: list[SmartCubeBinds.Command] = []
        for item in yml_dict["bindings"]:
            for command in item["commands"]:
                command_key = list(command.keys())[0]
                command_value = list(command.values())[0]
                if CommandKeys.from_str(command_key) == CommandKeys.TEXT:
                    commands.append(SmartCubeBinds.TextCommand(command_value))
                if CommandKeys.from_str(command_key) == CommandKeys.KEYS:
                    commands.append(SmartCubeBinds.KeyCommand(command_value))
                if CommandKeys.from_str(command_key) == CommandKeys.SHELL:
                    commands.append(SmartCubeBinds.ShellCommand(command_value))
                if CommandKeys.from_str(command_key) == CommandKeys.COMBO:
                    commands.append(SmartCubeBinds.KeyCombinationCommand(command_value))
                if CommandKeys.from_str(command_key) == CommandKeys.SLEEP:
                    commands.append(SmartCubeBinds.SleepCommand(command_value))

        config.bindings.update(
            SmartCubeMoves.MoveList().from_list(moves), SmartCubeBinds.CommandList(commands)
        )

        return config
