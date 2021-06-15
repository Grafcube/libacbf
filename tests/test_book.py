import os
import json
from pathlib import PurePath
from tests.conftest import book, sample_path

dir = f"tests/results/{PurePath(sample_path).name}/"
os.makedirs(dir, exist_ok=True)

def test_book():
	op = {
		"sample": sample_path,
		"file_path": str(book.book_path),
		"archive_type": book.archive.type.name if book.archive is not None else None,
		"namespace": book.namespace
	}
	with open(dir + "test_book.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))
