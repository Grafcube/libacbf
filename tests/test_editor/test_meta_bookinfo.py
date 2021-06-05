import os
import json
from pathlib import Path
from tests.conftest import book, sample_path
import libacbf.editor as edit
from libacbf.structs import Author

dir = f"tests/results/editor/{Path(sample_path).name}/metadata/book_info/"
os.makedirs(dir, exist_ok=True)

def test_authors():
	op = {"original": []}
	for i in book.Metadata.book_info.authors:
		new_op = {
			"activity": i.activity.name if i.activity is not None else None,
			"lang": i.lang,
			"first_name": i.first_name,
			"last_name": i.last_name,
			"middle_name": i.middle_name,
			"nickname": i.nickname,
			"home_page": i.home_page,
			"email": i.email
		}
		op["original"].append(new_op)
	with open(dir + "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit.metadata.bookinfo.authors.add(book, Author("Test"))
	op["added"] = []
	for i in book.Metadata.book_info.authors:
		new_op = {
			"activity": i.activity.name if i.activity is not None else None,
			"lang": i.lang,
			"first_name": i.first_name,
			"last_name": i.last_name,
			"middle_name": i.middle_name,
			"nickname": i.nickname,
			"home_page": i.home_page,
			"email": i.email
		}
		op["added"].append(new_op)
	with open(dir + "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

	n = book.Metadata.book_info.authors[-1].copy()
	n.first_name = "TheFirst"
	n.last_name = "TheLast"
	n.nickname = None
	n.home_page = "https://example.com/testing"
	edit.metadata.bookinfo.authors.edit(book, -1, n)
	op["edited"] = []
	for i in book.Metadata.book_info.authors:
		new_op = {
			"activity": i.activity.name if i.activity is not None else None,
			"lang": i.lang,
			"first_name": i.first_name,
			"last_name": i.last_name,
			"middle_name": i.middle_name,
			"nickname": i.nickname,
			"home_page": i.home_page,
			"email": i.email
		}
		op["edited"].append(new_op)
	with open(dir + "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

	edit.metadata.bookinfo.authors.remove(book, -1)
	op["removed"] = []
	for i in book.Metadata.book_info.authors:
		new_op = {
			"activity": i.activity.name if i.activity is not None else None,
			"lang": i.lang,
			"first_name": i.first_name,
			"last_name": i.last_name,
			"middle_name": i.middle_name,
			"nickname": i.nickname,
			"home_page": i.home_page,
			"email": i.email
		}
		op["removed"].append(new_op)
	with open(dir + "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))
