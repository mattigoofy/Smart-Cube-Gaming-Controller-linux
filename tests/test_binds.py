import json
import os
import random
import string
from itertools import product

import pytest

from src.SmartCubeGamingController.python_utils.bind_reader import (
    upload_binds,
    upload_binds_json,
    upload_binds_txt,
)
from src.SmartCubeGamingController.python_utils.binds_mode import _find_match

random.seed(42)

POSSIBLE_SOLUTIONS = ["R", "R'", "L", "L'", "U", "U'", "D", "D'", "F", "F'", "B", "B'"]
POSSIBLE_MODIFIERS = ["alt", "ctrl", "shift"]
POSSIBLE_KEYS = (
    ["tab", "space", "enter", "backspace"]
    + list(string.ascii_lowercase)
    + [str(i) for i in range(10)]
)
POSSIBLE_TIMES = [f"{round(t, 1)}s" for t in [0.5, 1.0, 2.0, 5.0, 10.0]]


def random_actions():
    """Generate a list of 1-3 actions for a bind"""
    actions = []
    for i in range(0, 3):
        kind = random.choice(["modifier+key", "key", "time"])
        if kind == "modifier+key":
            modifiers = random.sample(POSSIBLE_MODIFIERS, k=random.randint(1, 2))
            actions.append(modifiers + [random.choice(POSSIBLE_KEYS)])
        elif kind == "key":
            actions.append([random.choice(POSSIBLE_KEYS)])
        else:
            actions.append([random.choice(POSSIBLE_TIMES)])
    return actions


# Bind_reader
def test_upload_binds():
    path = "very invalid path"

    with pytest.raises(ValueError) as excinfo:
        upload_binds(path)


def test_upload_binds_txt():
    PATH = "test_binds/valid.txt"
    MAX_MOVES = 3

    solution_binds = {}
    for length in range(1, MAX_MOVES + 1):  # 1 through 4 moves
        for combo in product(POSSIBLE_SOLUTIONS, repeat=length):
            solution_binds[combo] = random_actions()

    solution_constants = {"deletion": "flush", "idle_time": 10.0}

    with open(PATH, "w") as file:
        for key, value in solution_constants.items():
            file.write(f"! {key} {value}\n")

        for combo, actions in solution_binds.items():
            moves = " ".join(combo)  # ('R', 'L\'') -> "R L'"
            actions_str = ""
            for a in actions:
                actions_str += "+".join(a) + " "
            file.write(f"{moves} - {actions_str}\n")

    binds, constants = upload_binds(PATH)
    assert binds == solution_binds
    assert constants == solution_constants

    binds, constants = upload_binds_txt(PATH)
    assert binds == solution_binds
    assert constants == solution_constants

    os.remove(PATH)


def test_upload_binds_json():
    PATH = "test_binds/valid.json"
    MAX_MOVES = 3

    solution_binds = {}
    for length in range(1, MAX_MOVES + 1):  # 1 through 4 moves
        for combo in product(POSSIBLE_SOLUTIONS, repeat=length):
            solution_binds[combo] = random_actions()

    solution_constants = {"deletion": "flush", "idle_time": 10.0}

    payload = []
    for key, value in solution_constants.items():
        payload.append(
            {"type": "Command", "name": key.upper(), "value": str(value).upper()}
        )
    for combo, actions in solution_binds.items():
        moves = " ".join(combo)
        actions_str = ""
        for a in actions:
            actions_str += "+".join(a) + " "

        payload.append({"type": "bind", "formula": moves, "keys": actions_str})

    with open(PATH, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)

    binds, constants = upload_binds(PATH)
    assert binds == solution_binds
    assert constants == solution_constants

    binds, constants = upload_binds_json(PATH)
    assert binds == solution_binds
    assert constants == solution_constants

    os.remove(PATH)


def test_find_match_greedy():
    MAX_MOVES = 3

    binds = {}
    for length in range(1, MAX_MOVES + 1):  # 1 through 4 moves
        for combo in product(POSSIBLE_SOLUTIONS, repeat=length):
            binds[combo] = []

    for bind in binds:
        match = _find_match(list(bind), binds, greedy=True)
        assert match == bind

    # test moves not in binds
    history = {}
    for combo in product(POSSIBLE_SOLUTIONS, repeat=MAX_MOVES + 1):
        history[combo] = []

    for h in history:
        match = _find_match(
            list(h), binds, greedy=True
        )  # find history with substrings as binds in valid binds
        assert match == tuple(list(h)[-MAX_MOVES:])


def test_find_match_exact():
    MAX_MOVES = 3

    # generate every possble combo for 4 moves
    binds = {}
    for length in range(1, MAX_MOVES + 1):  # 1 through 4 moves
        for combo in product(POSSIBLE_SOLUTIONS, repeat=length):
            binds[combo] = []

    for bind in binds:
        match = _find_match(list(bind), binds, exact=True)
        assert match == bind

    # test invalid moves
    invalid_binds = {}
    for combo in product(POSSIBLE_SOLUTIONS, repeat=MAX_MOVES + 1):
        invalid_binds[combo] = []

    for bind in invalid_binds:
        match = _find_match(
            list(bind), binds, exact=True
        )  # find invalid bind in valid binds
        assert match is None
