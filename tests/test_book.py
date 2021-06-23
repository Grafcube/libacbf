import os
import json
from pathlib import Path
from tests.testres import samples
from libacbf import ACBFBook

dir = Path("tests/results/test_book/")
os.makedirs(str(dir), exist_ok=True)

def test_book():
	for sample_path in samples.values():
		with ACBFBook(sample_path) as book:
			op = {
				"sample": sample_path,
				"book_path": str(book.book_path),
				"savable": book.mode,
				"savable": book.savable,
				"archive_name": book.archive.filename if book.archive is not None else None,
				"archive_type": book.archive.type.name if book.archive is not None else None,
				"namespace": book._namespace
			}
			with open(dir/f"test_book_{Path(sample_path).name}.json", 'w', encoding="utf-8", newline='\n') as result:
				result.write(json.dumps(op, ensure_ascii=False))


