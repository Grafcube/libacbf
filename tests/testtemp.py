from pprint import pprint
from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	pprint(book.Metadata.book_info.content_rating)
	print('')
	edit.metadata.bookinfo.rating.edit(book, "16+", "Age Rating")
	pprint(book.Metadata.book_info.content_rating)
	print('')
	edit.metadata.bookinfo.rating.remove(book, "Age Rating")
	pprint(book.Metadata.book_info.content_rating)
