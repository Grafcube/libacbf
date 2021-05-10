import os
from pathlib import Path
from tests.conftest import book, sample_path

dir = f"tests/results/{Path(sample_path).name}/metadata/publish_info/"
os.makedirs(dir, exist_ok=True)

def test_publisher():
	print(book.Metadata.publisher_info.publisher)
	with open(dir + "test_publishinfo_publisher.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.publisher_info.publisher)

def test_publish_date_string():
	print(book.Metadata.publisher_info.publish_date_string)
	with open(dir + "test_publishinfo_publish_date_string.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.publisher_info.publish_date_string)

def test_publish_date():
	print(book.Metadata.publisher_info.publish_date)
	with open(dir + "test_publishinfo_publish_date.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(str(book.Metadata.publisher_info.publish_date))

def test_city():
	print(book.Metadata.publisher_info.publish_city)
	with open(dir + "test_publishinfo_city.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.publisher_info.publish_city)

def test_isbn():
	print(book.Metadata.publisher_info.isbn)
	with open(dir + "test_publishinfo_isbn.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.publisher_info.isbn)

def test_license():
	print(book.Metadata.publisher_info.license)
	with open(dir + "test_publishinfo_license.txt", 'w', encoding="utf-8", newline='\n') as result:
		result.write(book.Metadata.publisher_info.license)
