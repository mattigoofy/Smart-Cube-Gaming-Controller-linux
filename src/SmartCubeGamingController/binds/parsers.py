import enum

from SmartCubeGamingController.binds.binds import (
    BindingsConfiguration,
    Command,
    CommandList,
    KeyCombinationCommand,
    KeyCommand,
    ShellCommand,
    SleepCommand,
    TextCommand,
)
from SmartCubeGamingController.binds.moves import MoveList, MoveType


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
    def parse(self, file_path: str) -> "BindingsConfiguration":
        extension = FileExtensions.from_str(file_path)
        parser = None

        if extension == FileExtensions.TXT:
            parser = ParserTXT()
        if extension == FileExtensions.JSON:
            parser = ParserJSON()
        if extension == FileExtensions.YAML:
            parser = ParserYML()

        if not parser:
            raise ValueError("No valid file extension found.")

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
            command_list:
            - text: abc def
            - keys: enter
            - shell: ls ~
            - combo: shift a
            - sleep: 5s
        """
        import yaml

        with open(file_path) as file:
            yml_dict = yaml.safe_load(file)

        config = BindingsConfiguration()
        config.deletion_type = yml_dict["deletion_type"]
        config.deletion_type = BindingsConfiguration.DeletionType.from_str(
            yml_dict["deletion_type"]
        )
        config.idle_time = float(yml_dict["idle_time"][:-1])  # remove 's'

        for item in yml_dict["bindings"]:
            moves_list: list[MoveType] = []
            moves = item["moves"].split()
            for move in moves:
                moves_list.append(MoveType.from_str(move))

            command_list: list[Command] = []
            for command in item["commands"]:
                command_key = list(command.keys())[0]
                command_value = list(command.values())[0]
                key = CommandKeys.from_str(command_key)

                if key == CommandKeys.TEXT:
                    command_list.append(TextCommand(command_value))
                if key == CommandKeys.KEYS:
                    command_list.append(KeyCommand(command_value))
                if key == CommandKeys.SHELL:
                    command_list.append(ShellCommand(command_value))
                if key == CommandKeys.COMBO:
                    combo_list = []
                    for combo_key in command_value.split():
                        combo_list.append(KeyCommand(combo_key))
                    command_list.append(KeyCombinationCommand(combo_list))
                if key == CommandKeys.SLEEP:
                    command_list.append(SleepCommand(float(command_value[:-1])))

            config.bindings.update(MoveList(moves_list), CommandList(command_list))

        return config
