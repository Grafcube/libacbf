from pprint import pprint
from libacbf import ACBFBook
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	print(book.book_path.name)
	print(book.archive.type if book.archive is not None else None)
