import SmartCubeGamingController.binds.moves as SmartCubeMoves
from src.SmartCubeGamingController.binds.binds import (
    BindingsConfiguration,
    Command,
    KeyCommand,
    CommandList,
    TextCommand,
)


class Parser:
    def parse(self, file_path: str) -> "BindingsConfiguration":
        raise NotImplementedError


class ParserTXT(Parser):
    def parse(self, file_path: str) -> "BindingsConfiguration":
        raise NotImplementedError


class ParserJSON(Parser):
    def parse(self, file_path: str) -> "BindingsConfiguration":
        raise NotImplementedError


class ParserYML(Parser):
    def parse(self, file_path: str) -> "BindingsConfiguration":
        """ Example file
        
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
        config.idle_time = yml_dict["idle_time"]
        moves: list[MoveType] = []
        for item in yml_dict["bindings"]:
            moves.append(item["moves"])

        commands: list[Command] = []
        for item in yml_dict["bindings"]:
            for command in item["commands"]:
                print(command)
                print(command.keys())
                if list(command.keys())[0] == "text":
                    commands.append(TextCommand(list(command.values())[0]))

        config.bindings.update(
            SmartCubeMoves.MoveList().from_list(moves), CommandList(commands)
        )

        return config
