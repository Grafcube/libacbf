import json
from libacbf.ACBFMetadata import ACBFMetadata

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.0.acbf"
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

# test_bookinfo_authors()
# test_bookinfo_titles()
# test_bookinfo_genres()
