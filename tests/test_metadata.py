import json
from libacbf.ACBFMetadata import ACBFMetadata

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book_metadata = ACBFMetadata(sample_path)

def test_bookinfo_authors():
	print(book_metadata.book_info.authors)
	with open("tests/results/metadata/test_bookinfo_authors.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.authors, ensure_ascii=False))

def test_bookinfo_titles():
	print(book_metadata.book_info.book_title)
	with open("tests/results/metadata/test_bookinfo_titles.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.book_title, ensure_ascii=False))

def test_bookinfo_genres():
	print(book_metadata.book_info.genres)
	with open("tests/results/metadata/test_bookinfo_genres.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.genres, ensure_ascii=False))

def test_bookinfo_annotations():
	print(book_metadata.book_info.annotations)
	with open("tests/results/metadata/test_bookinfo_annotations.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.annotations, ensure_ascii=False))

def test_bookinfo_characters():
	print(book_metadata.book_info.characters)
	with open("tests/results/metadata/test_bookinfo_characters.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.characters, ensure_ascii=False))

def test_bookinfo_keywords():
	print(book_metadata.book_info.keywords)
	with open("tests/results/metadata/test_bookinfo_keywords.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.keywords, ensure_ascii=False))

def test_bookinfo_series():
	print(book_metadata.book_info.series)
	with open("tests/results/metadata/test_bookinfo_series.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.series, ensure_ascii=False))

# test_bookinfo_authors()
# test_bookinfo_titles()
# test_bookinfo_genres()
# test_bookinfo_annotations()
# test_bookinfo_characters()
# test_bookinfo_keywords()
# test_bookinfo_series()
