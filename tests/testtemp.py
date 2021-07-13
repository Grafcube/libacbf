from pprint import pprint
from libacbf import ACBFBook
from tests.testres import samples

with ACBFBook(samples["cbz"]) as book:
    pprint(book.Metadata.book_info.book_title)
