from pprint import pprint
from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testsettings import samples

with ACBFBook("temp/self.acbf", 'w', False, "utf-16-be") as book:
	edit.metadata.bookinfo.authors.edit(book, 0, first_name="Hugh", last_name="Mann", nickname="NotAPlatypus")
