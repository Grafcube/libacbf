from libacbf.libacbf import ACBFBook
import os
import json
from pathlib import Path
from typing import Dict

dir = Path("tests/results/")
os.makedirs(str(dir), exist_ok=True)

def test_data(read_books: Dict[str, ACBFBook]):
	for path, book in read_books.items():
		op_dir = dir/Path(path).name
		os.makedirs(str(op_dir), exist_ok=True)
		op = {}
		for i in book.Data.files.keys():
			op[i] = {
				"type": book.Data[i].type,
				"is_embedded": book.Data[i].is_embedded,
				"filesize": len(book.Data[i].data)
			}
		with open(str(op_dir/"test_binary_data.json"), 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))
