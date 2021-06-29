from pprint import pprint
from libacbf import ACBFBook
import tests.testres as res
from lxml import etree

# with ACBFBook(r"tests/samples/Doctorow, Cory - Craphound-1.1.acbf") as book:
# 	pprint(book.Styles.list_styles())

with open(r"tests/samples/Doctorow, Cory - Craphound-1.1.acbf", 'r', encoding="utf-8") as xml:
	root = etree.fromstring(bytes(xml.read(), "utf-8"))

	el = root.getprevious()
	while True:
		if el.target == "xml-stylesheet":
			pprint(el.attrib)
		el = el.getprevious()
		if el is None:
			break
