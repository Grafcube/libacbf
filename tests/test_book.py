from libacbf.ACBFBook import ACBFBook
from tests.testsettings import samples

with ACBFBook(samples[2]) as book:
	pg = book.Body[12]
	print(pg.image_ref)
	print(pg.image.filesize)
