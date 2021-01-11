import json
from libacbf.ACBFMetadata import ACBFMetadata

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.0.acbf"

def test_bookinfo():
	book_metadata = ACBFMetadata(sample_path)
	print(book_metadata.book_info.authors)
	with open("tests/results/test_bookinfo.json", "w", encoding="utf-8", newline="\n") as result_bookinfo:
		result_bookinfo.write(json.dumps(book_metadata.book_info.authors, ensure_ascii=False))

test_bookinfo()
