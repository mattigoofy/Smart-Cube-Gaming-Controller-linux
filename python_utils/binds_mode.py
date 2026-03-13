import queue
import threading
import time

from .bind_reader import upload_binds
from .directinput import execute_combo
from .server import binds_reload_event, move_queue


def _find_match(history: list, binds: dict, greedy: bool = False):
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
    
    if greedy:
        return greedy_search(history, binds)
    else:
        for formula in binds:
            # Check for partially completed formulas
            for length in range(1, len(formula)):
                prefix = formula[:length]
                if len(history) >= length and tuple(history[-length:]) == prefix:
                    return None  # Still potentially mid-sequence, wait for more moves
                
        # No formula can grow further, find the longest possible sequence now
        return greedy_search(history, binds)


def run_binds_mode(stop_event: threading.Event):
    binds, constants = upload_binds()
    move_history: list[str] = []
    last_move_time = time.time()

    while not stop_event.is_set():
        if binds_reload_event.is_set():
            binds, constants = upload_binds()
            binds_reload_event.clear()
            print("Binds reloaded.")

        try:
            move = move_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        now = time.time()
        if now - last_move_time > constants["idle_time"]:
            move_history.clear()
        last_move_time = now

        move_history.append(move)

        match = _find_match(move_history, binds)
        if match:
            print(match)
            execute_combo(binds[match])
            if constants["delete_mode"] == "flush":
                move_history.clear()
            elif constants["delete_mode"] == "postfix":
                del move_history[-len(match) :]
