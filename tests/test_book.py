import json
from libacbf.ACBFBook import ACBFBook
from tests.testsettings import sample_path

book = ACBFBook(sample_path)

def test_book():
	op = {
		"sample": sample_path,
		"file_path": book.file_path,
		"archive_type": book.archive.type.name if book.archive is not None else None,
		"namespace": book.namespace.ACBFns_raw
	}
	with open("tests/results/test_book.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))
	book.close()
