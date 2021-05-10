import os
import json
from pathlib import Path
from tests.conftest import book, sample_path

dir = f"tests/results/{Path(sample_path).name}/"
os.makedirs(dir, exist_ok=True)

def test_references():
	print(book.References)
	with open(dir + "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(book.References, ensure_ascii=False))
