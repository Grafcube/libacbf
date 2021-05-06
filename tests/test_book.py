from libacbf.ACBFBook import ACBFBook
from py7zr.py7zr import SevenZipFile

samples = ["tests/samples/Doctorow, Cory - Craphound-1.0.acbf",
		"tests/samples/Doctorow, Cory - Craphound.cbz",
		"tests/samples/Doctorow, Cory - Craphound.cb7"
		]

# with SevenZipFile(samples[2], 'r') as archive:
# 	contents = list(archive.read(["image.jpg"]).values())[0].read()

with ACBFBook(samples[1]) as book:
	pg = book.Body[5]
	print(pg.image_ref)
	print(pg.image.filesize)
