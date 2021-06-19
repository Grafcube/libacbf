from pprint import pprint
from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testsettings import samples

with ACBFBook("temp/Doctorow, Cory - Craphound.cbz", 'a') as book:
	pprint([(x.dbname, x.reference, x.type) for x in book.Metadata.book_info.database_ref])
	edit.metadata.bookinfo.databaseref.add(book, "Test DB", "0123456", "ID")
	pprint([(x.dbname, x.reference, x.type) for x in book.Metadata.book_info.database_ref])
