from SmartCubeGamingController.tools.huffman import HuffmanTable, HuffmanTree
from SmartCubeGamingController.tools.unicode_frequency_analysis import WikipediaDumpCharacterCounter

import SmartCubeGamingController.modes.binds.moves as SmartCubeMoves


def main():
    counter = WikipediaDumpCharacterCounter("src/data/datasets/simplewiki-latest-pages-articles-multistream.xml")
    counter.count(10000)
    counter.save_frequencies("src/data/character_usage_analysis/temp")

    tree = HuffmanTree(degree=12)
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
    # table.to_bindfile("src/data/mappings/temp.txt", sort_type=HuffmanTable.SortType.ShortestFirst)

if __name__ == "__main__":
    # Full pipeline, from wiki dump to bindfile
    main()
