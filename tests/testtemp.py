from io import BytesIO
from pprint import pprint
from zipfile import ZipFile
from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testsettings import samples

file = BytesIO()

with ACBFBook(file, 'w') as book:
	edit.metadata.bookinfo.authors.edit(book, 0, first_name="Hugh", last_name="Mann", nickname="NotAPlatypus")

arc = ZipFile(file)
pprint(arc.namelist())
file.close()
