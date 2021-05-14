from libacbf.ACBFBook import ACBFBook
from tests.conftest import samples

with ACBFBook(samples[1]) as book:
	print(book.Metadata.book_info.book_title["en"])
	print(book.Body[4].image_ref)
	pg_iter = iter(book.Body)
	while True:
		try:
			pg = next(pg_iter)
			print(pg.image_ref, pg.image.filesize)
		except StopIteration:
			break
