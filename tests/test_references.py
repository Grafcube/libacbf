import json
from libacbf.ACBFBook import ACBFBook

sample_path = "tests/samples/Doctorow, Cory - Craphound.cbz"
book = ACBFBook(sample_path)
book.close()

def test_references():
	print(book.References)
	with open("tests/results/test_references.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book.References, ensure_ascii=False))
