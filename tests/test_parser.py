import textwrap

import pytest

from SmartCubeGamingController.binds.binds import (
    BindingsConfiguration,
    CommandList,
    KeyCombinationCommand,
    KeyCommand,
    ShellCommand,
    SleepCommand,
    TextCommand,
)
from SmartCubeGamingController.binds.moves import MoveList, MoveType
from SmartCubeGamingController.binds.parsers import (
    Parser,
    ParserJSON,
    ParserTXT,
    ParserYML,
)


def command_to_debug_tuple(cmd):
    from SmartCubeGamingController.binds.binds import (
        KeyCombinationCommand,
        KeyCommand,
        ShellCommand,
        SleepCommand,
        TextCommand,
    )

    if isinstance(cmd, TextCommand):
        return ("TextCommand", cmd.text)
    if isinstance(cmd, KeyCommand):
        return ("KeyCommand", cmd.key)
    if isinstance(cmd, ShellCommand):
        return ("ShellCommand", cmd.shell_command)
    if isinstance(cmd, SleepCommand):
        return ("SleepCommand", cmd.sleep_time)
    if isinstance(cmd, KeyCombinationCommand):
        # works even if parser accidentally stored wrong type in `combination`
        combo = cmd.combination
        if isinstance(combo, list):
            combo_vals = [getattr(k, "key", str(k)) for k in combo]
        else:
            combo_vals = combo
        return ("KeyCombinationCommand", combo_vals)

    return (type(cmd).__name__, str(cmd))


def command_list_to_debug_list(command_list):
    return [command_to_debug_tuple(c) for c in command_list.commands]


@pytest.fixture
def bind_config_solution():
    bc = BindingsConfiguration()
    bc.idle_time = 10.0
    bc.deletion_type = BindingsConfiguration.DeletionType.Flush

    bc.bindings.update(
        MoveList([MoveType.U, MoveType.R, MoveType.U_PRIME, MoveType.R_PRIME]),
        CommandList(
            [
                TextCommand("abc def"),
                KeyCommand("enter"),
                ShellCommand("ls ~"),
                KeyCombinationCommand([KeyCommand("shift"), KeyCommand("a")]),
                SleepCommand(5),
            ]
        ),
    )
    bc.bindings.update(
        MoveList([MoveType.B, MoveType.B_PRIME, MoveType.B, MoveType.B_PRIME]),
        CommandList(
            [
                TextCommand("abc def"),
                ShellCommand("ls ~"),
                KeyCombinationCommand([KeyCommand("shift"), KeyCommand("a")]),
            ]
        ),
    )

    return bc


class TestParser:
    def test_parser_yml(self, bind_config_solution: "BindingsConfiguration"):
        import os
        import tempfile
        YML  = """\
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
          - moves: B B' B B' 
            commands:
            - text: abc def
            - shell: ls ~
            - combo: shift a
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(textwrap.dedent(YML))
            name = f.name

        parser = ParserYML()
        bind_config = parser.parse(name)

        assert bind_config.deletion_type == bind_config_solution.deletion_type
        assert bind_config.idle_time == bind_config_solution.idle_time
        for moves, commands in bind_config.bindings.bindings.items():
            print(i for i in moves)
            # print(i for i in commands)
        assert len(bind_config.bindings.bindings) == len(
            bind_config_solution.bindings.bindings
        )

        assert set(bind_config.bindings.bindings.keys()) == set(
            bind_config.bindings.bindings.keys()
        )
        for moves in bind_config_solution.bindings.bindings:
            assert (
                bind_config.bindings.bindings[moves]
                == bind_config_solution.bindings.bindings[moves]
            ), (
                f"moves: {list(moves)}\nbindings: {command_list_to_debug_list(bind_config.bindings.bindings[moves])}"
            )
        assert bind_config.bindings == bind_config_solution.bindings
        assert bind_config == bind_config_solution
