import queue
import threading
import time

from .bind_reader import upload_binds
from .directinput import execute_combo
from .server import binds_reload_event, clear_binds_buffer, move_queue, set_binds_buffer


def _find_match(history: list, binds: dict, greedy: bool = False, exact: bool = False):
    """
    Tries to find a key combination in the current move history.

    Args:
        history (list)
        binds (list)
        greedy (bool): When True, it tries to find the shortest occurrence. When False, it finds the longest. Example: `F R U B U'`, with `U` and `R U B` as valid bindings. When greedy, it finds `U`, and immediately returns `U`, when not greedy, it first finds `R`, then `R U` (and doesn't return `U`), then `R U B`, and returns `R U B`.
    """

    def greedy_search(history: list, binds: dict):
        best, best_len = None, 0
        for formula in binds:
            n = len(formula)
            if n <= len(history) and tuple(history[-n:]) == formula and n > best_len:
                best, best_len = formula, n
        return best

    def exact_search(history: list, binds: dict):
        for formula in binds:
            if tuple(history) == formula:
                return formula

        return None

    if greedy:
        return greedy_search(history, binds)
    if exact:
        return exact_search(history, binds)
    else:
        for formula in binds:
            print(formula)
            # Check for partially completed formulas
            for length in range(1, len(formula)):
                prefix = formula[:length]
                print(prefix)
                print(tuple(history[-length:]))
                if len(history) >= length and tuple(history[-length:]) == prefix:
                    return None  # Still potentially mid-sequence, wait for more moves
            print()
        # No formula can grow further, find the longest possible sequence now
        return greedy_search(history, binds)


def run_binds_mode(stop_event: threading.Event, binds_path):
    binds, constants = upload_binds(binds_path)
    move_history: list[str] = []
    last_move_time = time.time()
    clear_binds_buffer()

    while not stop_event.is_set():
        if binds_reload_event.is_set():
            binds, constants = upload_binds(binds_path)
            binds_reload_event.clear()
            print("Binds reloaded.")

        try:
            move = move_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        now = time.time()
        if now - last_move_time > constants["idle_time"]:
            move_history.clear()
            set_binds_buffer(move_history)
        last_move_time = now

        move_history.append(move)
        set_binds_buffer(move_history)

        match = _find_match(move_history, binds, exact=True)
        if match:
            print(match)
            execute_combo(binds[match])
            if constants["deletion"] == "flush":
                move_history.clear()
            elif constants["deletion"] == "postfix":
                del move_history[-len(match) :]
            set_binds_buffer(move_history)

    clear_binds_buffer()
