from SmartCubeGamingController.tools.huffman import HuffmanTable, HuffmanTree
from SmartCubeGamingController.tools.unicode_frequency_analysis import WikipediaDumpCharacterCounter


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
    table.to_bindfile("src/data/mappings/temp.txt", sort_type=HuffmanTable.SortType.ShortestFirst)

if __name__ == "__main__":
    # Full pipeline, from wiki dump to bindfile
    main()
