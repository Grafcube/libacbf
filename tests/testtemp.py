from pprint import pprint
from libacbf import ACBFBook

with ACBFBook(r"tests/samples/Doctorow, Cory - Craphound-1.1.acbf") as book:
	pprint(book.Styles.list_styles())
