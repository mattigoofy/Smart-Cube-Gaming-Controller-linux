"""
N-ary Huffman implementation
https://arxiv.org/pdf/2105.07073
"""

import enum
import heapq
import json
import math
from types import SimpleNamespace

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
        self._mapping: dict[str, str] = {}
        self._binary_digit_mapping: dict[int, str] = {}

    @property
    def mapping(self):
        if not self._mapping:
            ValueError("No mapping available. Please generate the table first.")
        return self._mapping

    def from_tree(self, root: HuffmanTree) -> "HuffmanTable":
        self.bits_per_edge = number_of_binary_digits(root.degree)
        self._mapping = {}
        self._walk(root.tree, "")
        return self

    def set_binary_digit_mapping(self, mapping: dict[int, str]):
        self._binary_digit_mapping = mapping

    def _walk(self, node: HuffmanTreeNode, code: str) -> None:
        if node.is_leaf():
            if not node.is_ghost():
                # Single-symbol edge case: give it the empty string (or "0")
                self.mapping[node.symbol] = code if code else "0"  # type: ignore
            return
        b = self.bits_per_edge
        for i, child in enumerate(node.children):
            if self._binary_digit_mapping:
                label = self._binary_digit_mapping[i]
                if label:
                    edge_label = label
                else:
                    edge_label = str(i)
            else:
                # Display as binary, for funsies
                edge_label = format(i, f"0{b}b")
            self._walk(child, code + edge_label)

    def dump(self, filepath: str):
        with open(filepath, "w") as file:
            file.write(self.__repr__())

    class SortType(enum.Enum):
        Alphabetically = enum.auto()
        ShortestFirst = enum.auto()

    def to_bindfile(self, filepath: str, sort_type: SortType | None = None):
        string_builder = ""

        sorted_list: list[tuple[str, str]] = []
        match sort_type:
            case self.SortType.Alphabetically:
                sorted_list = sorted(self.mapping.items(), key=lambda kv: kv[0])
            case self.SortType.ShortestFirst:
                sorted_list = sorted(self.mapping.items(), key=lambda kv: len(kv[1]))
            case _:
                sorted_list = sorted(self.mapping.items())

        for key, value in sorted_list:
            # Special cases
            match key:
                case "\n":
                    string_builder += f"{value}- enter\n"
                case "\t":
                    string_builder += f"{value}- tab\n"
                case " ":
                    string_builder += f"{value}- space\n"
                case _:
                    string_builder += f"{value}- {key}\n"

        with open(filepath, "w") as file:
            file.write(string_builder)

    def __repr__(self) -> str:
        lines = [
            f"HuffmanTable (bits_per_edge={self.bits_per_edge}, {len(self.mapping)} symbols)"
        ]
        for sym, code in sorted(self.mapping.items(), key=lambda kv: len(kv[1])):
            display = repr(sym) if (sym.isspace() or not sym.isprintable()) else sym
            lines.append(f"  {display:20s}  ->  {code}")
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
            0: "R ",
            1: "R' ",
            2: "L ",
            3: "L' ",
            4: "U ",
            5: "U' ",
            6: "B ",
            7: "B' ",
            8: "D ",
            9: "D' ",
            10: "F ",
            11: "F' ",
        }
    )
    table.from_tree(tree)
    # table.to_bindfile(
    #     "binds/full_huffman_mapping.txt",
    #     sort_type=HuffmanTable.SortType.ShortestFirst,
    # )
    # table.to_bindfile('tools/data/mappings/mapping_tiny.txt', sort_type=HuffmanTable.SortType.ShortestFirst)
    table.to_bindfile("src/data/mappings/temp.txt", sort_type=HuffmanTable.SortType.ShortestFirst)


if __name__ == "__main__":
    main()
