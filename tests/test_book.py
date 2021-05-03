from libacbf.Editor import BookManager
from libacbf.ACBFBook import ACBFBook

samples = ["tests/samples/Doctorow, Cory - Craphound-1.1.acbf",
		"tests/samples/Doctorow, Cory - Craphound.cbz"
		]

with ACBFBook(samples[1]) as book:
	print(book.Body[4].image.filesize)
