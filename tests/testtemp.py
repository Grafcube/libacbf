from pprint import pprint
from libacbf import ACBFBook
import tests.testres as res

with ACBFBook(res.samples["cbz"]) as book:
	pprint([x.__dict__ for x in book.Metadata.book_info.authors])
