from libacbf import ACBFBook
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	print(book.Metadata.book_info.book_title["en"])
	for i in book.Body.pages:
		print(i.image_ref, i.image.filesize)
