"""
Tests for BindingsConfiguration._from_txt (the plain-text binding parser).
"""

import textwrap
import pytest

from SmartCubeGamingController.binds.binds import (
    BindingsConfiguration,
    Command,
    KeyCombinationCommand,
    CommandList,
    KeyCommand,
    SleepCommand,
    _parse_command_list,  # pyright: ignore[reportPrivateUsage]
    _parse_command_token,  # pyright: ignore[reportPrivateUsage]
    _parse_move_list,  # pyright: ignore[reportPrivateUsage]
)
from SmartCubeGamingController.binds.moves import MoveType, MoveList


def make_config(txt: str) -> BindingsConfiguration:
    """Write txt to a temp file and parse it."""
    import tempfile, os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(textwrap.dedent(txt))
        name = f.name
    try:
        return BindingsConfiguration().from_file(name)
    finally:
        os.unlink(name)


def ml(*moves: MoveType) -> MoveList:
    return MoveList().from_list(list(moves))


def kcl(*commands: Command) -> CommandList:
    return CommandList(list(commands))


def sc(c: str) -> KeyCommand:
    return KeyCommand(c)


def kc(*keys: str) -> KeyCombinationCommand:
    return KeyCombinationCommand([sc(k) for k in keys])


def sleep(s: float) -> SleepCommand:
    return SleepCommand(s)


class TestParseCommandToken:
    def test_single_character(self):
        assert _parse_command_token("a") == sc("a")

    def test_named_key(self):
        assert _parse_command_token("space") == sc("space")
        assert _parse_command_token("enter") == sc("enter")

    def test_dash_is_single_character(self):
        # '-' is a valid KeyCommand, not a separator
        assert _parse_command_token("-") == sc("-")

    def test_key_combination_two(self):
        assert _parse_command_token("ctrl+t") == kc("ctrl", "t")

    def test_key_combination_three(self):
        assert _parse_command_token("ctrl+alt+t") == kc("ctrl", "alt", "t")

    def test_sleep_integer(self):
        assert _parse_command_token("10s") == sleep(10.0)

    def test_sleep_float(self):
        assert _parse_command_token("1.5s") == sleep(1.5)

    def test_sleep_zero(self):
        assert _parse_command_token("0s") == sleep(0.0)


class TestParseCommandList:
    def test_single_token(self):
        assert _parse_command_list("space") == kcl(sc("space"))

    def test_combination_token(self):
        assert _parse_command_list("alt+tab") == kcl(kc("alt", "tab"))

    def test_mixed_tokens(self):
        result = _parse_command_list("alt+space c o d e 1.0s enter")
        assert result == kcl(
            kc("alt", "space"),
            sc("c"),
            sc("o"),
            sc("d"),
            sc("e"),
            sleep(1.0),
            sc("enter"),
        )

    def test_bare_dash_command(self):
        # The RHS after splitting on ' - ' may itself be '-'
        assert _parse_command_list("-") == kcl(sc("-"))


class TestParseMoveList:
    def test_single_move(self):
        assert _parse_move_list("R") == ml(MoveType.R)

    def test_prime_move(self):
        assert _parse_move_list("R'") == ml(MoveType.R_PRIME)

    def test_multiple_moves(self):
        assert _parse_move_list("R U R' U'") == ml(
            MoveType.R, MoveType.U, MoveType.R_PRIME, MoveType.U_PRIME
        )

    def test_unknown_token_raises(self):
        with pytest.raises(ValueError, match="Unknown move token"):
            _parse_move_list("R X")


class TestFromTxt:
    def test_simple_binding(self):
        cfg = make_config("""\
            R R - ctrl+t
        """)
        assert cfg.bindings.bindings[ml(MoveType.R, MoveType.R)] == kcl(kc("ctrl", "t"))

    def test_config_deletion_flush(self):
        cfg = make_config("""\
            ! DELETION FLUSH
            R R - ctrl+t
        """)
        assert cfg.deletion_type == "FLUSH"

    def test_config_idle_time(self):
        cfg = make_config("""\
            ! IDLE_TIME 10
            R R - ctrl+t
        """)
        assert cfg.idle_time == 10.0

    def test_comment_lines_skipped(self):
        cfg = make_config("""\
            # this is a comment
            R R - ctrl+t
        """)
        assert len(cfg.bindings.bindings) == 1

    def test_blank_lines_skipped(self):
        cfg = make_config("""\

            R R - ctrl+t

        """)
        assert len(cfg.bindings.bindings) == 1

    def test_inline_comment_stripped(self):
        cfg = make_config("""\
            F F - ctrl+alt+t    # terminal
        """)
        assert cfg.bindings.bindings[ml(MoveType.F, MoveType.F)] == kcl(
            kc("ctrl", "alt", "t")
        )

    def test_binding_with_sleep(self):
        cfg = make_config("""\
            B B - shift+10.0s
        """)
        assert cfg.bindings.bindings[ml(MoveType.B, MoveType.B)] == kcl(
            kc("shift", "10.0s")  # shift+10.0s is one combination token
        )

    def test_binding_sleep_standalone(self):
        # A sleep as its own token (not joined with '+')
        cfg = make_config("""\
            R U - 1.5s enter
        """)
        assert cfg.bindings.bindings[ml(MoveType.R, MoveType.U)] == kcl(
            sleep(1.5), sc("enter")
        )

    def test_binding_dash_command(self):
        # The command itself is a literal '-'
        cfg = make_config("""\
            R - -
        """)
        assert cfg.bindings.bindings[ml(MoveType.R)] == kcl(sc("-"))

    def test_binding_space_command(self):
        cfg = make_config("""\
            F R - space
        """)
        assert cfg.bindings.bindings[ml(MoveType.F, MoveType.R)] == kcl(sc("space"))

    def test_complex_command_sequence(self):
        cfg = make_config("""\
            L' U' L U - alt+space c o d e 1.0s enter    # open vscode
        """)
        expected_moves = ml(
            MoveType.L_PRIME,
            MoveType.U_PRIME,
            MoveType.L,
            MoveType.U,
        )
        expected_commands = kcl(
            kc("alt", "space"),
            sc("c"),
            sc("o"),
            sc("d"),
            sc("e"),
            sleep(1.0),
            sc("enter"),
        )
        assert cfg.bindings.bindings[expected_moves] == expected_commands

    def test_full_example_file(self):
        """Parse complete example."""
        cfg = make_config("""\
            ! DELETION FLUSH
            ! IDLE_TIME 10
            R L' - alt+tab
            R R - ctrl+t
            R U R' U' - ctrl+z
            F R - space
            F F - ctrl+alt+t                            # terminal
            L' U' L U - alt+space c o d e 1.0s enter    # open vscode
            # comment
        """)
        assert cfg.deletion_type == "FLUSH"
        assert cfg.idle_time == 10.0
        assert len(cfg.bindings.bindings) == 6

        assert cfg.bindings.bindings[ml(MoveType.R, MoveType.L_PRIME)] == kcl(
            kc("alt", "tab")
        )
        assert cfg.bindings.bindings[ml(MoveType.R, MoveType.R)] == kcl(kc("ctrl", "t"))
        assert cfg.bindings.bindings[
            ml(MoveType.R, MoveType.U, MoveType.R_PRIME, MoveType.U_PRIME)
        ] == kcl(kc("ctrl", "z"))

    def test_missing_separator_raises(self):
        with pytest.raises(ValueError, match="separator"):
            make_config("R R ctrl+t\n")

    def test_unknown_config_directive_raises(self):
        with pytest.raises(ValueError, match="Unknown config directive"):
            make_config("! UNKNOWN_THING foo\n")

    def test_bad_idle_time_raises(self):
        with pytest.raises(ValueError, match="IDLE_TIME"):
            make_config("! IDLE_TIME notanumber\n")
