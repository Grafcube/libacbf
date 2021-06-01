from pprint import pprint
from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	pprint([{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages])
	print('')
	edit.metadata.bookinfo.languagelayers.add(book, "kn", True)
	pprint([{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages])
	print('')
	edit.metadata.bookinfo.languagelayers.edit(book, 1, "ta", False)
	pprint([{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages])
	print('')
