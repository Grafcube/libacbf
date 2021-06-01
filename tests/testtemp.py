from pprint import pprint
from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	pprint([{"title": x.title, "seq": x.sequence, "vol": x.volume} for x in book.Metadata.book_info.series.values()])
	print('')
	edit.metadata.bookinfo.series.edit(book, "test", "1")
	pprint([{"title": x.title, "seq": x.sequence, "vol": x.volume} for x in book.Metadata.book_info.series.values()])
	print('')
	edit.metadata.bookinfo.series.edit(book, "test", volume="2")
	pprint([{"title": x.title, "seq": x.sequence, "vol": x.volume} for x in book.Metadata.book_info.series.values()])
