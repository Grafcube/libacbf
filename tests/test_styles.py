import os
import json
from pathlib import Path
from tests.conftest import book, sample_path

dir = f"tests/results/{Path(sample_path).name}/styles/"
os.makedirs(dir, exist_ok=True)

def test_styles():
	print(book.Styles.list_styles())
	for i in book.Styles.list_styles():
		with open(dir + i, 'w', encoding="utf-8", newline='\n') as st_output:
			st_output.write(book.Styles[i])
	with open(dir + "test_styles.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(book.Styles.list_styles(), ensure_ascii=False))

def test_stylesheet():
	print(book.Stylesheet)
	with open(dir + "test_stylesheet.css", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Stylesheet if book.Stylesheet is not None else "")
