import os
import json
from pathlib import Path
from tests.conftest import book, sample_path, get_au_op

dir = f"tests/results/{Path(sample_path).name}/metadata/document_info/"
os.makedirs(dir, exist_ok=True)

def test_authors():
	op = []
	for i in book.Metadata.document_info.authors:
		op.append(get_au_op(i))
	print(op)
	with open(dir + "test_documentinfo_authors.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_creation_date_string():
	print(book.Metadata.document_info.creation_date_string)
	with open(dir + "test_documentinfo_creation_date_string.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.document_info.creation_date_string)

def test_creation_date():
	print(book.Metadata.document_info.creation_date)
	with open(dir + "test_documentinfo_creation_date.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(str(book.Metadata.document_info.creation_date))

def test_source():
	print(book.Metadata.document_info.source)
	with open(dir + "test_documentinfo_source.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.document_info.source)

def test_id():
	print(book.Metadata.document_info.document_id)
	with open(dir + "test_documentinfo_id.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.document_info.document_id)

def test_version():
	print(book.Metadata.document_info.document_version)
	with open(dir + "test_documentinfo_version.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.document_info.document_version)

def test_history():
	print(book.Metadata.document_info.document_history)
	with open(dir + "test_documentinfo_history.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(book.Metadata.document_info.document_history, ensure_ascii=False))
