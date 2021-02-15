from lxml import etree

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"

with open(sample, "r", encoding="utf-8") as book:
	contents = book.read()
	root = etree.fromstring(bytes(contents, encoding="utf-8"))

	print(r"{" + root.nsmap[None] + r"}")
