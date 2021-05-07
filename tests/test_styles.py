import json
from libacbf.ACBFBook import ACBFBook

sample_path = "tests/samples/Doctorow, Cory - Craphound.cb7"
book = ACBFBook(sample_path)
book.close()

def test_styles():
	print(book.Styles.list_styles())
	for i in book.Styles.list_styles():
		with open(f"tests/results/styles/{i}", "w", encoding="utf-8", newline="\n") as st_output:
			st_output.write(book.Styles[i])
	with open("tests/results/styles/test_styles.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book.Styles.list_styles(), ensure_ascii=False))

def test_stylesheet():
	print(book.Stylesheet)
	with open(f"tests/results/styles/test_stylesheet.css", "w", encoding="utf-8", newline="\n") as result:
		result.write(book.Stylesheet)
