import json
import re
import wikitextparser as wtp
from collections import Counter
from xml.etree.ElementTree import iterparse


# Wikipedia XML namespaces vary by dump; the namespace URI is embedded in the root tag.
# We detect it dynamically so the script works with any dump.
def get_namespace(element_tag: str) -> str:
    """Extract '{namespace}' prefix from a tag like '{http://...}mediawiki'."""
    if element_tag.startswith("{"):
        return element_tag.split("}")[0] + "}"
    return ""


def plain_text_from_wikitext(raw: str) -> str:
    """Strip wikitext markup and return plain prose."""
    parsed = wtp.parse(raw)

    # Needs manual processing, as parsed.plain_text() apparently doesn't cleanly remove everything

    # 1. Remove gallery tags and their contents entirely
    #    (wikitextparser exposes these as Tags)
    for tag in parsed.get_tags():
        if tag.name.lower() in ("gallery", "ref", "references", "math",
                "syntaxhighlight", "source", "code",
                "nowiki", "score", "timeline"):
            tag.string = ""
 
    # 2. Remove File:/Image: wikilinks (they're not prose)
    for wl in parsed.wikilinks:
        if wl.title.startswith(("File:", "Image:", "Category:")):
            wl.string = ""
 
    text = parsed.plain_text()
 
    # 3. Strip heading markers left by plain_text()  (== Heading ==)
    text = re.sub(r"={2,}[^=\n]+={2,}", "", text)
 
    # 4. Strip bullet / numbered list markers at line start
    text = re.sub(r"^[*#:;]+\s*", "", text, flags=re.MULTILINE)
 
    # 5. Strip any remaining File:/Image:/Category: lines
    #    (can survive as plain text after wikilink stripping)
    text = re.sub(r"^(File|Image|Category):[^\n]*", "", text, flags=re.MULTILINE | re.IGNORECASE)
 
    # 6. Collapse runs of whitespace / blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
 
    return text.strip()


def iter_article_texts(xml_path: str):
    """
    Generator: yield plain-text content of each non-redirect article.

    Uses iterparse in 'end' mode so each <page> element is fully built
    before we process it, then immediately discarded to keep memory flat.
    """
    ns = None  # will be set on first element

    # We track a small state machine per page
    in_page = False
    is_redirect = False
    current_text = None

    for event, elem in iterparse(xml_path, events=("start", "end")):
        # Detect namespace from the very first element
        if ns is None:
            ns = get_namespace(elem.tag)

        tag = elem.tag  # e.g. '{http://www.mediawiki.org/xml/export-0.11/}page'

        if event == "start":
            if tag == f"{ns}page":
                in_page = True
                is_redirect = False
                current_text = None

        elif event == "end":
            if not in_page:
                elem.clear()
                continue

            if tag == f"{ns}redirect":
                # <redirect> element present -> skip this page
                is_redirect = True

            elif tag == f"{ns}text":
                # The article wikitext lives here
                current_text = elem.text or ""

            elif tag == f"{ns}page":
                # Page fully parsed, process if it's a real article
                if not is_redirect and current_text:
                    try:
                        yield plain_text_from_wikitext(current_text)
                    except Exception:
                        # Malformed wikitext, skip silently
                        pass

                # Clear the element and all its children so the GC can reclaim them.
                elem.clear()
                in_page = False

            else:
                # For all other tags inside a page we don't need to keep them
                elem.clear()


def count_characters_wiki(xml_path: str, limit: int | None = None) -> Counter[str]:
    counter: Counter[str] = Counter()
    pages_processed = 0

    for text in iter_article_texts(xml_path):
        counter.update(text)
        pages_processed += 1

        if pages_processed % 1000 == 0:
            print(f"  {pages_processed:,} articles processed, "
                  f"{len(counter):,} unique chars so far…", flush=True)

        if limit and pages_processed >= limit:
            print(f"Reached --limit {limit}, stopping early.")
            break

    print(f"\nDone. {pages_processed:,} articles, {len(counter):,} unique characters.")
    return counter


def count_characters_generic(filepath: str, limit: int | None = None) -> Counter[str]:
    counter: Counter[str] = Counter()

    with open(filepath, 'r') as file:
        counter.update(file.read())

    print(f"\nDone. {len(counter):,} unique characters.")
    return counter


def save_frequencies(counter: Counter[str], output_path: str) -> None:
    # Sort by frequency descending; store as [[char, count], ...] for JSON portability
    sorted_items = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    data = {
        "total_chars": sum(counter.values()),
        "unique_chars": len(counter),
        "frequencies": [[ch, count] for ch, count in sorted_items],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Frequencies saved to: {output_path}")


def print_top(counter: Counter[str], n: int = 30) -> None:
    print(f"\nTop {n} characters:")
    print(f"{'Rank':>5}  {'Char':>6}  {'Codepoint':>10}  {'Count':>12}  {'Name'}")
    print("-" * 65)
    import unicodedata
    for rank, (ch, count) in enumerate(counter.most_common(n), 1):
        try:
            name = unicodedata.name(ch)
        except ValueError:
            name = "(no name)"
        cp = f"U+{ord(ch):04X}"
        display = repr(ch) if ch.isspace() else ch
        print(f"{rank:>5}  {display:>6}  {cp:>10}  {count:>12,}  {name}")


def main():
    limit = None
    # counter = count_characters_wiki('tools/data/simplewiki-latest-pages-articles-multistream.xml', limit=limit)
    counter = count_characters_generic("tools/data/sample_text_simplified.txt")
    print_top(counter, n=30)
    # save_frequencies(counter, 'tools/data/character_usage_frequencies')
    save_frequencies(counter, 'tools/data/character_usage_frequencies_tiny')


if __name__ == "__main__":
    main()
