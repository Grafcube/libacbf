import json
from pathlib import Path
from typing import Dict
from libacbf import ACBFBook

def test_book_props(read_books: Dict[Path, ACBFBook]):
	for dir, book in read_books.items():
		op = {
			"book_path": str(book.book_path),
			"savable": book.mode,
			"savable": book.savable,
			"archive_name": book.archive.filename if book.archive is not None else None,
			"archive_type": book.archive.type.name if book.archive is not None else None,
			"namespace": book._namespace
		}
		with open(dir/"test_book_props.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))
