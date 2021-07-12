import json
from pathlib import Path
from typing import Tuple
from libacbf import ACBFBook

def test_references(read_books: Tuple[Path, ACBFBook]):
    dir, book = read_books
    with open(dir / "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(book.References, ensure_ascii=False))
