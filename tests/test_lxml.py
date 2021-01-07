import os
from lxml import etree

sample = "tests/samples/Doctorow, Cory - Craphound-1.0.acbf"

ACBFns = r"{http://www.fictionbook-lib.org/xml/acbf/1.0}"

with open(sample, "r") as book:
	root = etree.fromstring(bytes(book.read(), encoding="utf-8"))
	tree = etree.ElementTree(root)
	# for i in list(root.find(f"{ACBFns}meta-data/{ACBFns}book-info")):
	# 	print(i.tag.replace(ACBFns, ""))
	# for i in list(root.find(f"{ACBFns}meta-data/{ACBFns}book-info/{ACBFns}author")):
	# 	print(i.tag.replace(ACBFns, ""))
	for i in list(root.findall(f"{ACBFns}meta-data/{ACBFns}book-info/{ACBFns}author")):
		print(i.attrib)
