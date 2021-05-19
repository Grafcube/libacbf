from libacbf import ACBFBook
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	print(book.Styles["_"])
