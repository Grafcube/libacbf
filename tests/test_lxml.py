import re
from lxml import etree

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"

with open(sample, "r", encoding="utf-8") as book:
	contents = book.read()
	root = etree.fromstring(bytes(contents, encoding="utf-8"))
	ACBFns = r"{" + root.nsmap[None] + r"}"

	for i in root.findall(f"{ACBFns}references/{ACBFns}reference"):
		print(i.attrib["id"])
