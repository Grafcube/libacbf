from libacbf.ACBFBook import ACBFBook

samples = ["tests/samples/Doctorow, Cory - Craphound-1.1.acbf",
		"tests/samples/Doctorow, Cory - Craphound.cbz"
		]
book = ACBFBook(samples[1])

print(book.Metadata.publisher_info.publisher)
