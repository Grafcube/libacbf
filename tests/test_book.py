from libacbf.Editor import BookManager
from libacbf.ACBFBook import ACBFBook

samples = ["tests/samples/Doctorow, Cory - Craphound-1.1.acbf",
		"tests/samples/Doctorow, Cory - Craphound.cbz"
		]

with ACBFBook(samples[1]) as book:
	img = book.Body[3].image
	if img is not None:
		print(img.id)
		print(img.filesize)
