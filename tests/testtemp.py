from io import BytesIO
from pathlib import Path
from pprint import pprint
from zipfile import ZipFile
# from libacbf import ACBFBook
# import libacbf.editor as edit
from tests.testsettings import samples

file = BytesIO()

# with ACBFBook(file, 'w') as book:
# 	edit.metadata.bookinfo.authors.edit(book, 0, first_name="Hugh", last_name="Mann", nickname="NotAPlatypus")

arc = ZipFile(file, 'r')
arc.writestr("something.txt", "aisufvaf")
pprint(arc.namelist())
print(arc.read("something.txt").decode("utf-8"))
arc.close()
file.close()
