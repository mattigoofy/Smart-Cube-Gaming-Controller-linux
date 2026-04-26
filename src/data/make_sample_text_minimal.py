import re

# 1) Make all characters uppercase
# 2) Only allow [A-Z] and '\n'

def process_file(filepath_in: str, filepath_out: str):
    file_content: str = ""
    with open(filepath_in, 'r') as file:
        file_content = file.read()

    file_minimized = file_content.upper()
    file_minimized = re.sub(r"[^A-Z\n ]+", "", file_minimized, flags=re.MULTILINE)

    with open(filepath_out, 'w') as file:
        file.write(file_minimized)

def main():
    process_file(filepath_in="src/data/datasets/sample_text.txt", filepath_out="src/data/datasets/sample_text_simplified.txt")

if __name__ == "__main__":
    main()
