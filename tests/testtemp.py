from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	print(book.References)
	edit.book.references.add(book, "test_ref", "This is a test reference")
	print(book.References)
	edit.book.references.remove(book, "ref_001")
	print(book.References)
