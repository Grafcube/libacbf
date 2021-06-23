from pprint import pprint
from libacbf import ACBFBook
from tests.testres import samples

with ACBFBook(samples["cbz"]) as book:
	pprint([x.__dict__ for x in book.Metadata.book_info.authors])
