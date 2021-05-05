import json
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book = ACBFBook(sample_path)
book.close()
book_metadata: ACBFMetadata = book.Metadata

def test_publisher():
	print(book_metadata.publisher_info.publisher)
	with open("tests/results/metadata/publish_info/test_publishinfo_publisher.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.publisher_info.publisher, ensure_ascii=False))

def test_publish_date_string():
	print(book_metadata.publisher_info.publish_date_string)
	with open("tests/results/metadata/publish_info/test_publishinfo_publish_date_string.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.publisher_info.publish_date_string, ensure_ascii=False))

def test_publish_date():
	print(book_metadata.publisher_info.publish_date)
	with open("tests/results/metadata/publish_info/test_publishinfo_publish_date.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(str(book_metadata.publisher_info.publish_date), ensure_ascii=False))

def test_city():
	print(book_metadata.publisher_info.publish_city)
	with open("tests/results/metadata/publish_info/test_publishinfo_city.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.publisher_info.publish_city, ensure_ascii=False))

def test_isbn():
	print(book_metadata.publisher_info.isbn)
	with open("tests/results/metadata/publish_info/test_publishinfo_isbn.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.publisher_info.isbn, ensure_ascii=False))

def test_license():
	print(book_metadata.publisher_info.license)
	with open("tests/results/metadata/publish_info/test_publishinfo_license.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.publisher_info.license, ensure_ascii=False))
