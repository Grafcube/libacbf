import json
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook
from tests.testsettings import sample_path

book = ACBFBook(sample_path)
book.close()
book_metadata: ACBFMetadata = book.Metadata

def test_authors():
	op = []
	for i in book_metadata.document_info.authors:
		new_op = {
			"activity": i.activity,
			"lang": i.lang,
			"first_name": i.first_name,
			"last_name": i.last_name,
			"middle_name": i.middle_name,
			"nickname": i.nickname,
			"home_page": i.home_page,
			"email": i.email
		}
		op.append(new_op)
	print(op)
	with open("tests/results/metadata/document_info/test_documentinfo_authors.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_creation_date_string():
	print(book_metadata.document_info.creation_date_string)
	with open("tests/results/metadata/document_info/test_documentinfo_creation_date_string.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.document_info.creation_date_string, ensure_ascii=False))

def test_creation_date():
	print(book_metadata.document_info.creation_date)
	with open("tests/results/metadata/document_info/test_documentinfo_creation_date.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(str(book_metadata.document_info.creation_date), ensure_ascii=False))

def test_source():
	print(book_metadata.document_info.source)
	with open("tests/results/metadata/document_info/test_documentinfo_source.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.document_info.source, ensure_ascii=False))

def test_id():
	print(book_metadata.document_info.document_id)
	with open("tests/results/metadata/document_info/test_documentinfo_id.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.document_info.document_id, ensure_ascii=False))

def test_version():
	print(book_metadata.document_info.document_version)
	with open("tests/results/metadata/document_info/test_documentinfo_version.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.document_info.document_version, ensure_ascii=False))

def test_history():
	print(book_metadata.document_info.document_history)
	with open("tests/results/metadata/document_info/test_documentinfo_history.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.document_info.document_history, ensure_ascii=False))
