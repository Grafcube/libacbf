import json
from lxml import etree
from libacbf.BodyInfo import TextArea

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"

with open(sample, "r") as book:
	root = etree.fromstring(bytes(book.read(), encoding="utf-8"))
	ACBFns = r"{" + root.nsmap[None] + r"}"

	tx_area = root.find(f"{ACBFns}body/{ACBFns}page/{ACBFns}text-layer/{ACBFns}text-area")

	for p in TextArea(tx_area, ACBFns).paragraph:
		print(p)
