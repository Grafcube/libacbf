import json
import os
from pathlib import Path
from typing import Tuple
from libacbf import ACBFBook


def make_style_dir(path):
    os.makedirs(path / "styles", exist_ok=True)
    return path / "styles"


def test_styles(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_style_dir(path)

    with open(dir / "test_styles.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(book.styles.list_styles(), ensure_ascii=False, indent='\t', separators=(', ', ': ')))

    for i in book.styles.list_styles():
        name = i
        if i == '_':
            name = "embedded.css"
        with open(dir / name, 'w', encoding="utf-8", newline='\n') as st_output:
            st_output.write(book.styles[i])
