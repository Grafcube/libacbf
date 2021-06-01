from pprint import pprint
from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	pprint([{x.dbname: {"ref": x.reference, "type": x.type}} for x in book.Metadata.book_info.database_ref])
	print('')
	edit.metadata.bookinfo.databaseref.add(book, "a_library", "123456", "id")
	edit.metadata.bookinfo.databaseref.add(book, "b_library", "https://example.com/id/123456", "url")
	pprint([{x.dbname: {"ref": x.reference, "type": x.type}} for x in book.Metadata.book_info.database_ref])
	print('')
	edit.metadata.bookinfo.databaseref.edit(book, 1, ref="654321")
	pprint([{x.dbname: {"ref": x.reference, "type": x.type}} for x in book.Metadata.book_info.database_ref])
	print('')
	edit.metadata.bookinfo.databaseref.edit(book, 1, ref="654321")
	pprint([{x.dbname: {"ref": x.reference, "type": x.type}} for x in book.Metadata.book_info.database_ref])
	# print('')
