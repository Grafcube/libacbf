import os
from pathlib import Path
from libacbf.ACBFBook import ACBFBook

samples = ["tests/samples/Doctorow, Cory - Craphound-1.1.acbf",
		"tests/samples/Doctorow, Cory - Craphound.cbz"
		]
book = ACBFBook(samples[1])

print(book.Metadata.publisher_info.publisher)

print(os.path.abspath(r"file:///C:/Users/Kirthi/Pictures/kana_keyboard.jpg"))
pt = Path(r"file:///C:/Users/Kirthi/Pictures/kana_keyboard.jpg")
print(pt.name)
print(pt.suffix)
print(pt.parent)
