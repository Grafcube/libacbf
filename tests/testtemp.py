from io import BytesIO
from pathlib import Path
from pprint import pprint
from zipfile import ZipFile
from rarfile import RarFile
from libacbf import ACBFBook
import libacbf.editor as edit
from tests.testres import samples

# file = BytesIO()

# with ACBFBook(samples["cbz"]) as book:
# 	pprint(book.Metadata.book_info.book_title)

# arc = ZipFile(file, 'r')
# arc.writestr("something.txt", "aisufvaf")
# pprint(arc.namelist())
# print(arc.read("something.txt").decode("utf-8"))
# arc.close()
# file.close()
