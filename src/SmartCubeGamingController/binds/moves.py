import enum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Use these imports only when type checking. This resolves a circular import issue when trying to run.
    from SmartCubeGamingController.binds.binds import Bindings


class MoveType(enum.Enum):
    """
    An abstraction of a move on the Rubik's cube
    """

    U = "U"
    U_PRIME = "U'"
    R = "R"
    R_PRIME = "R'"
    L = "L"
    L_PRIME = "L'"
    F = "F"
    F_PRIME = "F'"
    B = "B"
    B_PRIME = "B'"
    D = "D"
    D_PRIME = "D'"


class MoveList:
    """
    A list of moves, for example ["U", "F'", "B"]
    """

    def __init__(self) -> None:
        self._move_list: list[MoveType] = []

    @property
    def move_list(self):
        return self._move_list

    def from_list(self, list: list[MoveType]):
        self._move_list = list
        return self

    def __iter__(self):
        return iter(self.move_list)

    def __len__(self):
        return len(self.move_list)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, MoveList):
            return NotImplemented
        return self.move_list == value.move_list

    def __hash__(self) -> int:
        return hash(tuple(self._move_list))


class MoveHistory:
    def __init__(self) -> None:
        self._history: list[MoveType] = []

    @property
    def history(self):
        return self._history

    def clear(self):
        self.history.clear()
        return self

    def append(self, move: MoveType):
        self.history.append(move)
        return self

    class ClearHistoryType(enum.Enum):
        All = enum.auto()
        OnlyMatched = enum.auto()

    # FIXME `clear` probably shouldn't be (another) responsibility of this function. Instead, the calling function should handle this.
    def find_match(
        self,
        bindings: "Bindings",
        greedy: bool = False,
        clear: ClearHistoryType = ClearHistoryType.All,
    ) -> MoveList | None:
        """
        Tries to find a move combination in the current move history.

        Args:
            bindings (Bindings): The set of bindings to check against.
            greedy (bool): When True, returns the most recent complete match (longest sequence ending at the tail of history). When False, returns the binding with the longest overlap with the tail of history, even if the match is incomplete.
            clear (ClearHistoryType): How to modify the history when a moveset was found. 'All' clears the whole history, 'OnlyMatched' clears only the matched portion.

        Returns:
            The matched MoveList, or None if nothing matched.
        """

        def _greedy_search(bindings: Bindings):
            best: MoveList | None = None
            best_end = -1

            for move_list in bindings.bindings.keys():
                moves = list(move_list)
                length = len(moves)
                if length > len(self.history):
                    # Skip MoveLists that are larger than the current history
                    continue
                # Scan all positions where this binding could end
                for end in range(length - 1, len(self.history)):
                    start = end - (length - 1)
                    if list(self.history[start : end + 1]) == moves:
                        # Found a complete match ending at `end`
                        length_best = len(best) if best else 0
                        if end > best_end or (end == best_end and length > length_best):
                            best_end = end
                            best = move_list
            return best

        def _non_greedy_search(bindings: Bindings):
            best: MoveList | None = None
            best_overlap = 0

            for move_list in bindings.bindings.keys():
                moves = list(move_list)
                length = len(moves)

                # Find the longest suffix of history that is a prefix of moves
                max_possible = min(length, len(self.history))
                overlap = 0
                for k in range(1, max_possible + 1):
                    if list(self.history[-k:]) == moves[:k]:
                        overlap = k

                if overlap > best_overlap:
                    best_overlap = overlap
                    best = move_list

            return best

        if greedy:
            return _greedy_search(bindings)
        else:
            return _non_greedy_search(bindings)
