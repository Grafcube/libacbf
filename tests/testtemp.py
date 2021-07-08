from pprint import pprint
from libacbf import ACBFBook

with ACBFBook(r"temp/fail.acbf", 'w') as book:
	pprint(book.Styles.list_styles())
