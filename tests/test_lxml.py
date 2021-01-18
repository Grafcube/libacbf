import os
from lxml import etree

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"

with open(sample, "r") as book:
	root = etree.fromstring(bytes(book.read(), encoding="utf-8"))
	ACBFns = r"{" + root.nsmap[None] + r"}"
	# print(root.nsmap)
	# for i in list(root.find(f"{ACBFns}meta-data")):
	# 	print(i.tag.replace(ACBFns, ""))
	# 	print(type(i))
	# for i in root.findall(f"{ACBFns}meta-data/{ACBFns}document-info/{ACBFns}source/{ACBFns}p"):
	# 	print(i.tag)
	print(type(root.find("adfbh")))

	# meta = root.find(f"{ACBFns}meta-data/{ACBFns}book-info/{ACBFns}characters")
	# print(type(meta))
	# for i in meta:
	# 	print(i.tag)
