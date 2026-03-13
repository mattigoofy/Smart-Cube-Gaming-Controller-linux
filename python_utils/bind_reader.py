"""
Created on Tue Oct 27 01:55:49 2020

@author: ImNotGLaDOS

find full code at: https://github.com/ImNotGLaDOS/gan-to-keyboard
"""

import json
import logging
import re

logger = logging.getLogger("Bind_Uploader")


def upload_binds(file_path:str) -> tuple[dict[tuple[str], list[list[str]]], dict[str, any]]:
    if file_path[-3:] == "txt":
        binds, constants = upload_binds_txt(file_path)
    elif file_path[-4:] == "json":
        binds, constants = upload_binds_json(file_path)
    else:
        raise ValueError('Unsupported filetype.')
    
    return binds, constants



def upload_binds_txt(
    file: str,
) -> tuple[dict[tuple[str], list[list[str]]], dict[str, any]]:
    """
    loads binds from binds.txt
    ret: dict[<formula>, [<key bind>, ...]], dict{'delete_mode': 'flush/postfix/keep', 'idle_time': float}
    """
    ret: dict[tuple[str], str] = {}
    constants = {"delete_mode": "flush", "idle_time": 10}
    with open(file) as file:
        binds = file.read()

        for bind in binds.split("\n"):
            # Empty line check
            if bind.strip() == "":
                continue

            # Deleting comments
            if bind.count("#") > 0:
                bind = bind[: bind.find("#")]
                if bind.strip() == "":
                    continue

            # Commands
            if bind[0] == "!":
                if len(bind[1:].strip().split()) != 2:
                    logger.warning(f'Not valid setting line: "{bind}"')

                name, value = bind[1:].strip().split()
                name = name.casefold()
                value = value.casefold()

                if name == "deletion":
                    if value not in ["keep", "postfix", "flush"]:
                        logger.warning(f'Not valid delete_mode: "{bind}"')
                    else:
                        constants[name] = value

                elif name == "idle_time":
                    try:
                        value = float(value)
                        constants[name] = value
                    except ValueError:
                        logger.warning(f'Not valid idle_time: "{bind}"')

                    continue

            # Regular binds
            if bind.count("-") != 1:
                logger.warning(f'Unreadable bind: "{bind}"')
                continue

            bind = bind.split("-")
            formula: list[str] = bind[0].strip().split()  # example: ['L', 'R\'', 'U2']
            keys_list: list[str] = (
                bind[1].strip().split()
            )  # ['ctrl+U', '0.5s', 'alt+tab']
            keys_list = [
                comb.split("+") for comb in keys_list
            ]  # [['ctrl', 'U'], ['0.5s'], ['alt', 'tab']]

            ret[tuple(formula)] = keys_list

    ret_repr = "\n".join([repr(bind) for bind in ret.items()])
    logger.info(f"Readed binds:\n{ret_repr}")
    return ret, constants


def upload_binds_json(
    file: str,
) -> tuple[dict[tuple[str], list[list[str]]], dict[str, any]]:
    """
    Loads binds from a JSON file.
    Returns: (binds dict, constants dict) — same shape as the .txt version.
    """
    binds: dict[tuple[str], list[list[str]]] = {}
    constants = {"delete_mode": "flush", "idle_time": 10}

    with open(file) as f:
        entries = json.load(f)

    for entry in entries:
        entry_type = entry.get("type", "").lower()

        # --- Commands / settings ---
        if entry_type == "command":
            name = entry.get("name", "").casefold()
            value = entry.get("value", "").casefold()

            if name == "deletion":
                if value not in ["keep", "postfix", "flush"]:
                    logger.warning(f"Invalid deletion value: '{value}'")
                else:
                    constants["delete_mode"] = value

            elif name == "idle_time":
                try:
                    constants["idle_time"] = float(value)
                except ValueError:
                    logger.warning(f"Invalid idle_time value: '{value}'")

            else:
                logger.warning(f"Unknown command: '{name}'")

        # --- Key binds ---
        elif entry_type == "bind":
            formula_str = entry.get("formula", "")
            keys_str = entry.get("keys", "")

            formula = tuple(formula_str.strip().split())
            keys_list = [comb.split("+") for comb in keys_str.strip().split()]
            binds[formula] = keys_list

        # --- Shell commands ---
        elif entry_type == "shell":
            formula_str = entry.get("formula", "")
            command = entry.get("command", "")

            formula = tuple(formula_str.strip().split())
            # Store shell commands wrapped so the caller can distinguish them
            binds[formula] = [["__shell__", command]]

        else:
            logger.warning(f"Unknown entry type: '{entry_type}'")

    ret_repr = "\n".join([repr(bind) for bind in binds.items()])
    logger.info(f"Loaded binds:\n{ret_repr}")
    return binds, constants
