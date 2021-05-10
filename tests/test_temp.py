from libacbf.ACBFBook import ACBFBook
from tests.conftest import samples

with ACBFBook(samples[4]) as book:
	print(book.Metadata.book_info.book_title)
	pg = book.Body[12]
	print(pg.image_ref)
	print(pg.image.filesize)
