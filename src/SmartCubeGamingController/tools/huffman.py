"""
N-ary Huffman implementation
https://arxiv.org/pdf/2105.07073
"""

import heapq
import json
import math
from types import SimpleNamespace

import SmartCubeGamingController.modes.binds.moves as SmartCubeMoves
import SmartCubeGamingController.modes.binds.binds as SmartCubeBinds

_GHOST_NODE_PREFIX: str = "GHOST_NODE_"


class HuffmanTreeNode:
    def __init__(self, frequency: int | float, symbol: str | None = None) -> None:
        self.symbol: str | None = symbol
        self.children: list[HuffmanTreeNode] = []
        self.frequency: int | float = frequency

    def __lt__(self, other: "HuffmanTreeNode") -> bool:
        return self.frequency < other.frequency

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def is_ghost(self) -> bool:
        return self.symbol is not None and self.symbol.startswith(_GHOST_NODE_PREFIX)


class HuffmanTree:
    """
    An n-ary Huffman tree.
    """

    def __init__(self, degree: int) -> None:
        self.degree: int = degree
        self._tree: HuffmanTreeNode | None = None
        self._symbol_distribution_table: list[tuple[str, int]]
        self._number_unique_symbols: int

    @property
    def tree(self):
        if not self._tree:
            raise ValueError("No tree available. Please generate the tree first.")
        return self._tree

    def set_frequency_analysis(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as file:
            raw_json = json.load(file, object_hook=SimpleNamespace)

            self._symbol_distribution_table = raw_json.frequencies

            # Add ghost nodes with frequency zero
            self._number_unique_symbols = raw_json.unique_chars
            number_ghost_nodes = number_of_placeholder_nodes(
                self.degree, self._number_unique_symbols
            )

            # TODO Is this a valid way to add ghost nodes? It's important to filter out these ghost nodes for the eventual Huffman table
            for i in range(number_ghost_nodes):
                self._symbol_distribution_table.append((_GHOST_NODE_PREFIX + str(i), 0))

    def generate(self) -> None:
        # Min-heap
        heap: list[HuffmanTreeNode] = []
        for symbol, frequency in self._symbol_distribution_table:
            node = HuffmanTreeNode(frequency, symbol)
            heapq.heappush(heap, node)

        n = self.degree
        while len(heap) > 1:
            children = [heapq.heappop(heap) for _ in range(min(n, len(heap)))]

            # Anonymous (internal) node
            parent = HuffmanTreeNode(frequency=sum(c.frequency for c in children))
            parent.children = children
            heapq.heappush(heap, parent)

        root = heap[0]
        self._tree = root


class HuffmanTable:
    """
    A mapping of every symbol to its Huffman code.
    """

    def __init__(self) -> None:
        self._mapping: dict[SmartCubeBinds.TextCommand, SmartCubeMoves.MoveList] = {}
        self._binary_digit_mapping: dict[int, SmartCubeMoves.MoveType] = {}

    @property
    def mapping(self):
        if not self._mapping:
            ValueError("No mapping available. Please generate the table first.")
        return self._mapping

    def from_tree(self, root: HuffmanTree) -> "HuffmanTable":
        self.bits_per_edge = number_of_binary_digits(root.degree)
        self._mapping = {}
        self._walk(root.tree, SmartCubeMoves.MoveList())
        return self

    def set_binary_digit_mapping(self, mapping: dict[int, SmartCubeMoves.MoveType]):
        self._binary_digit_mapping = mapping

    def _walk(self, node: HuffmanTreeNode, move_list: SmartCubeMoves.MoveList) -> None:
        if node.is_leaf():
            if not node.is_ghost():
                if not node.symbol:
                    raise ValueError(
                        f"Expected node {node} to have a symbol associated with it, it did not."
                    )
                text = SmartCubeBinds.TextCommand(node.symbol)
                move = SmartCubeMoves.MoveType(move_list)
                self.mapping[text] = SmartCubeMoves.MoveList(moves=[move])
            return

        for i, child in enumerate(node.children):
            new_move = str(i)
            if self._binary_digit_mapping:
                label = self._binary_digit_mapping[i]
                new_move = label
            new_move = SmartCubeMoves.MoveType(new_move)

            # Doing this instead of using MoveList.append(), because we shouldn't mutate the parameter variable.
            new_move_list = [move for move in move_list]
            new_move_list.append(new_move)
            self._walk(child, SmartCubeMoves.MoveList(new_move_list))

    def dump(self, filepath: str):
        with open(filepath, "w") as file:
            file.write(self.__repr__())

    def to_bindings(self) -> SmartCubeBinds.Bindings:
        binds = SmartCubeBinds.Bindings()

        for text_command, move_list in self.mapping.items():
            binds.update(move_list, SmartCubeBinds.CommandList([text_command]))

        return binds

    def __repr__(self) -> str:
        lines = [
            f"HuffmanTable (bits_per_edge={self.bits_per_edge}, {len(self.mapping)} symbols)"
        ]
        for text_command, move_list in sorted(
            self.mapping.items(), key=lambda kv: len(kv[1])
        ):
            lines.append(f"  {text_command:20s}  ->  {move_list}")
        return "\n".join(lines)


def number_of_placeholder_nodes(degree: int, number_distinct_symbols: int) -> int:
    """
    For n-ary Huffman trees, you need to insert a certain number of 'ghost leaf nodes' that have a probability of zero, to make the math work out.
    """
    n = degree
    if n <= 2:
        return 0
    s = number_distinct_symbols
    return (n - 2) - ((s + n - 3) % (n - 1))


def number_of_binary_digits(degree: int) -> int:
    """
    Number of binary digits required to represent a number of degree `degree`. For example, to represent '5' we need at least three binary digits (0b000 through 0b101)
    """
    return math.ceil(math.log2(degree))


def main():
    tree = HuffmanTree(degree=12)
    # tree.set_frequency_analysis('tools/data/character_usage_frequencies_5000_articles.json')
    # tree.set_frequency_analysis("tools/data/character_usage_frequencies_full")
    # tree.set_frequency_analysis("tools/data/character_usage_frequencies_full_backspace")
    # tree.set_frequency_analysis('tools/data/character_usage_frequencies_tiny')
    tree.set_frequency_analysis("src/data/character_usage_analysis/temp")
    tree.generate()
    table = HuffmanTable()
    table.set_binary_digit_mapping(
        {
            0: SmartCubeMoves.MoveType.R,
            1: SmartCubeMoves.MoveType.R_PRIME,
            2: SmartCubeMoves.MoveType.L,
            3: SmartCubeMoves.MoveType.L_PRIME,
            4: SmartCubeMoves.MoveType.U,
            5: SmartCubeMoves.MoveType.U_PRIME,
            6: SmartCubeMoves.MoveType.B,
            7: SmartCubeMoves.MoveType.B_PRIME,
            8: SmartCubeMoves.MoveType.D,
            9: SmartCubeMoves.MoveType.D_PRIME,
            10: SmartCubeMoves.MoveType.F,
            11: SmartCubeMoves.MoveType.F_PRIME,
        }
    )
    table.from_tree(tree)
    # table.to_bindfile(
    #     "binds/full_huffman_mapping.txt",
    #     sort_type=HuffmanTable.SortType.ShortestFirst,
    # )
    # table.to_bindfile('tools/data/mappings/mapping_tiny.txt', sort_type=HuffmanTable.SortType.ShortestFirst)
    # table.to_bindfile("src/data/mappings/temp.txt", sort_type=HuffmanTable.SortType.ShortestFirst)


if __name__ == "__main__":
    main()
