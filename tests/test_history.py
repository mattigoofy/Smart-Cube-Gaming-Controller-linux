import pytest

from SmartCubeGamingController.binds.binds import (
    Bindings,
    CommandList,
    SingleCharacterCommand,
)
from SmartCubeGamingController.binds.moves import MoveHistory, MoveList, MoveType


@pytest.fixture
def history():
    moves = [
        MoveType.U_PRIME,
        MoveType.L_PRIME,
        MoveType.R_PRIME,
        MoveType.U,
    ]
    history = MoveHistory()
    for move in moves:
        history.append(move)
    return history


@pytest.fixture
def bindings():
    binds = Bindings()

    # In history, small string
    bind1 = (
        MoveList().from_list([MoveType.R_PRIME]),
        CommandList([SingleCharacterCommand("A")]),
    )

    # In history, longer string
    bind2 = (
        MoveList().from_list([MoveType.U_PRIME, MoveType.L_PRIME, MoveType.R_PRIME]),
        CommandList([SingleCharacterCommand("B")]),
    )

    # Not in history
    bind3 = (
        MoveList().from_list([MoveType.B_PRIME]),
        CommandList([SingleCharacterCommand("C")]),
    )

    # In history, long string, more recent, incomplete
    bind4 = (
        MoveList().from_list([MoveType.L_PRIME, MoveType.R_PRIME, MoveType.U, MoveType.R]),
        CommandList([SingleCharacterCommand("D")]),
    )

    binds.update(bind1[0], bind1[1])
    binds.update(bind2[0], bind2[1])
    binds.update(bind3[0], bind3[1])
    binds.update(bind4[0], bind4[1])

    return binds

@pytest.fixture
def bindings2():
    binds = Bindings()

    # In history, small string
    bind1 = (
        MoveList().from_list([MoveType.R_PRIME]),
        CommandList([SingleCharacterCommand("A")]),
    )

    # In history, longer string
    bind2 = (
        MoveList().from_list([MoveType.U_PRIME, MoveType.L_PRIME, MoveType.R_PRIME]),
        CommandList([SingleCharacterCommand("B")]),
    )

    # In history, longer string, more recent
    bind3 = (
        MoveList().from_list([MoveType.L_PRIME, MoveType.R_PRIME, MoveType.U]),
        CommandList([SingleCharacterCommand("B")]),
    )

    # Not in history
    bind4 = (
        MoveList().from_list([MoveType.B_PRIME]),
        CommandList([SingleCharacterCommand("C")]),
    )

    binds.update(bind1[0], bind1[1])
    binds.update(bind2[0], bind2[1])
    binds.update(bind3[0], bind3[1])
    binds.update(bind4[0], bind4[1])

    return binds

@pytest.fixture
def bindings3():
    binds = Bindings()

    # In history, small string
    bind1 = (
        MoveList().from_list([MoveType.R_PRIME, MoveType.U]),
        CommandList([SingleCharacterCommand("A")]),
    )

    # Not fully in history
    bind2 = (
        MoveList().from_list([MoveType.U, MoveType.L_PRIME]),
        CommandList([SingleCharacterCommand("B")]),
    )

    binds.update(bind1[0], bind1[1])
    binds.update(bind2[0], bind2[1])

    return binds


class TestMoveHistory:
    def test_history_greedy(self, history: MoveHistory, bindings: Bindings):
        match = history.find_match(bindings, greedy=True)

        # Should return longest, most recent complete match
        assert match == MoveList().from_list([MoveType.U_PRIME, MoveType.L_PRIME, MoveType.R_PRIME])

    def test_history_non_greedy(self, history: MoveHistory, bindings: Bindings):
        match = history.find_match(bindings, greedy=False)
        
        # Should return longest possible match given the history, even if it's incomplete
        assert match == MoveList().from_list([MoveType.L_PRIME, MoveType.R_PRIME, MoveType.U, MoveType.R])

    def test_history_non_greedy2(self, history: MoveHistory, bindings2: Bindings):
        match = history.find_match(bindings2, greedy=False)
        
        # Should return longest possible match given the history, even if it's incomplete
        # Should return the most recent match if length is the tie-breaker
        assert match == MoveList().from_list([MoveType.L_PRIME, MoveType.R_PRIME, MoveType.U])

    def test_history_non_greedy3(self, history: MoveHistory, bindings3: Bindings):
        match = history.find_match(bindings3, greedy=False)
        
        # Both options are the _same length_, one is already in buffer, the other is not fully in the buffer.
        # Should pick the one that _is_ in the buffer, over the one that's not fully in the buffer.
        assert match == MoveList().from_list([MoveType.R_PRIME, MoveType.U])
