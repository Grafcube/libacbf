import json
import os
from pathlib import Path
from typing import Dict
from libacbf import ACBFBook

def make_style_dir(path):
	os.makedirs(path/"styles", exist_ok=True)
	return path/"styles"

def test_styles(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_style_dir(path)
		for i in book.Styles.list_styles():
			name = i
			if i == "_":
				name = "embedded.css"
			with open(dir/name, 'w', encoding="utf-8", newline='\n') as st_output:
				st_output.write(book.Styles[i])
		with open(dir/"test_styles.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(book.Styles.list_styles(), ensure_ascii=False))
