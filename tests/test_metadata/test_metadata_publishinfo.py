from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook
from tests.testsettings import sample_path

book = ACBFBook(sample_path)
book.close()
book_metadata: ACBFMetadata = book.Metadata

def test_publisher():
	print(book_metadata.publisher_info.publisher)
	with open("tests/results/metadata/publish_info/test_publishinfo_publisher.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book_metadata.publisher_info.publisher)

def test_publish_date_string():
	print(book_metadata.publisher_info.publish_date_string)
	with open("tests/results/metadata/publish_info/test_publishinfo_publish_date_string.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book_metadata.publisher_info.publish_date_string)

def test_publish_date():
	print(book_metadata.publisher_info.publish_date)
	with open("tests/results/metadata/publish_info/test_publishinfo_publish_date.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(str(book_metadata.publisher_info.publish_date))

def test_city():
	print(book_metadata.publisher_info.publish_city)
	with open("tests/results/metadata/publish_info/test_publishinfo_city.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book_metadata.publisher_info.publish_city)

def test_isbn():
	print(book_metadata.publisher_info.isbn)
	with open("tests/results/metadata/publish_info/test_publishinfo_isbn.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book_metadata.publisher_info.isbn)

def test_license():
	print(book_metadata.publisher_info.license)
	with open("tests/results/metadata/publish_info/test_publishinfo_license.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book_metadata.publisher_info.license)
