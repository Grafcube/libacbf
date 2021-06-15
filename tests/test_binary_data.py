import os
import json
from pathlib import PurePath
from tests.conftest import book, sample_path

dir = f"tests/results/{PurePath(sample_path).name}/"
os.makedirs(dir, exist_ok=True)

def test_data():
	op = {}
	for i in book.Data.files.keys():
		op[i] = {
			"type": book.Data[i].type,
			"is_embedded": book.Data[i].is_embedded,
			"filesize": len(book.Data[i].data)
		}
	print(op)
	with open(dir + "test_binary_data.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))
