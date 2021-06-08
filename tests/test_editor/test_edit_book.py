import os
import json
from pathlib import Path
from tests.conftest import book, sample_path
import libacbf.editor as edit_bookinfo

dir = f"tests/results/{Path(sample_path).name}/editor/"
os.makedirs(dir, exist_ok=True)

def test_references():
	op = {"original": book.References}
	with open(dir + "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_bookinfo.book.references.edit(book, "test_ref", "This is a new test reference.")
	op["added"] = book.References
	with open(dir + "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_bookinfo.book.references.edit(book, "test_ref", "This is an edited test reference.")
	op["edited"] = book.References
	with open(dir + "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_bookinfo.book.references.remove(book, "test_ref")
	op["removed"] = book.References
	with open(dir + "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_bookinfo.book.references.remove(book, "test_ref")
	op["non-existant"] = book.References
	with open(dir + "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_data():
	pass

def test_styles():
	pass
