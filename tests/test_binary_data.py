import json
from pathlib import Path
from typing import Dict
from libacbf.libacbf import ACBFBook

def test_embedded(read_books: Dict[Path, ACBFBook]):
	for dir, book in read_books.items():
		op = {}
		for i in book.Data.files.keys():
			op[i] = {
				"type": book.Data[i].type,
				"is_embedded": book.Data[i].is_embedded,
				"filesize": len(book.Data[i].data)
			}
		with open(dir/"test_binary_data.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))
