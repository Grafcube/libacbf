from libacbf.ACBFBook import ACBFBook
from py7zr.py7zr import SevenZipFile

samples = ["tests/samples/Doctorow, Cory - Craphound-1.0.acbf",
		"tests/samples/Doctorow, Cory - Craphound.cbz",
		"tests/samples/Doctorow, Cory - Craphound.cb7"
		]

with ACBFBook(samples[2]) as book:
	pg = book.Body[0]
	print(pg.image_ref)
	print(pg.image.filesize)
