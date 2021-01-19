import json
from libacbf.ACBFMetadata import ACBFMetadata

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book_metadata = ACBFMetadata(sample_path)

def test_authors():
	print(book_metadata.document_info.authors)
	with open("tests/results/metadata/document_info/test_documentinfo_authors.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.document_info.authors, ensure_ascii=False))

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
