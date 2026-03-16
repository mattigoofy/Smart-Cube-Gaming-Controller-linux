import enum
from typing import List

from binds.binds import (
    BindingsConfiguration,
    Command,
    CommandList,
    KeyCombinationCommand,
    KeyCommand,
    ShellCommand,
    SleepCommand,
    TextCommand,
)

import SmartCubeGamingController.binds.moves as SmartCubeMoves


class FileExtensions(enum.Enum):
    TXT = "txt"
    JSON = "json"
    YAML = "yml"

    @staticmethod
    def from_str(filepath):
        if filepath[-3:].lower() in ("txt"):
            return FileExtensions.TXT
        if filepath[-4:].lower() in ("json"):
            return FileExtensions.JSON
        if filepath[-3:].lower() in ("yml") or filepath[-4:].lower() in ("yaml"):
            return FileExtensions.YAML


class CommandKeys(enum.Enum):
    TEXT = "text"
    KEYS = "keys"
    SHELL = "shell"
    COMBO = "combo"
    SLEEP = "sleep"

    @staticmethod
    def from_str(value):
        try:
            return CommandKeys(value)
        except ValueError:
            return None


class Parser:
    def parse(self, file_path: str) -> "BindingsConfiguration":
        if FileExtensions.from_str(file_path) == FileExtensions.TXT:
            parser = ParserTXT()
            return parser.parse(file_path)
        if FileExtensions.from_str(file_path) == FileExtensions.JSON:
            parser = ParserJSON()
            return parser.parse(file_path)
        if FileExtensions.from_str(file_path) == FileExtensions.YAML:
            parser = ParserYML()
            return parser.parse(file_path)


class ParserTXT(Parser):
    def parse(self, file_path: str) -> "BindingsConfiguration":
        raise NotImplementedError


class ParserJSON(Parser):
    def parse(self, file_path: str) -> "BindingsConfiguration":
        raise NotImplementedError


class ParserYML(Parser):
    def parse(self, file_path: str) -> "BindingsConfiguration":
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

        config = BindingsConfiguration()
        config.deletion_type = yml_dict["deletion_type"]
        config.idle_time = float(yml_dict["idle_time"][:-1])  # remove 's'
        moves: list[MoveType] = []
        for item in yml_dict["bindings"]:
            moves.append(item["moves"])

        commands: list[Command] = []
        for item in yml_dict["bindings"]:
            for command in item["commands"]:
                command_key = list(command.keys())[0]
                command_value = list(command.values())[0]
                if CommandKeys.from_str(command_key) == CommandKeys.TEXT:
                    commands.append(TextCommand(command_value))
                if CommandKeys.from_str(command_key) == CommandKeys.KEYS:
                    commands.append(KeyCommand(command_value))
                if CommandKeys.from_str(command_key) == CommandKeys.SHELL:
                    commands.append(ShellCommand(command_value))
                if CommandKeys.from_str(command_key) == CommandKeys.COMBO:
                    commands.append(KeyCombinationCommand(command_value))
                if CommandKeys.from_str(command_key) == CommandKeys.SLEEP:
                    commands.append(SleepCommand(command_value))

        config.bindings.update(
            SmartCubeMoves.MoveList().from_list(moves), CommandList(commands)
            SmartCubeMoves.MoveList().from_list(moves), CommandList(commands)
        )

        return config
