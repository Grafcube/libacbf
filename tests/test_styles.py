import json
from libacbf.ACBFBook import ACBFBook

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book = ACBFBook(sample_path)

def test_styles():
	print(book.styles)
	with open("tests/results/styles/test_styles.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book.styles, ensure_ascii=False))

def test_stylesheet():
	print(book.Stylesheet)
	with open(f"tests/results/styles/test_stylesheet.css", "w", encoding="utf-8", newline="\n") as result:
		result.write(book.Stylesheet)
