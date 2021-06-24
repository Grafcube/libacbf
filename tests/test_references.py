import json
from pathlib import Path
from typing import Dict
from libacbf import ACBFBook

def test_references(read_books: Dict[Path, ACBFBook]):
	for dir, book in read_books.items():
		with open(dir/"test_references.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(book.References, ensure_ascii=False))
