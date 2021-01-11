import os
from lxml import etree

sample = "tests/samples/Doctorow, Cory - Craphound-1.0.acbf"

ACBFns = r"{http://www.fictionbook-lib.org/xml/acbf/1.0}"

with open(sample, "r") as book:
	root = etree.fromstring(bytes(book.read(), encoding="utf-8"))
	# for i in list(root.find(f"{ACBFns}meta-data")):
	# 	print(i.tag.replace(ACBFns, ""))
	# 	print(type(i))
	# for i in list(root.find(f"{ACBFns}meta-data/{ACBFns}book-info")):
	# 	print(i.tag.replace(ACBFns, ""))
	# for i in list(root.find(f"{ACBFns}meta-data/{ACBFns}book-info/{ACBFns}author")):
	# 	print(i.tag.replace(ACBFns, ""))
	# for i in list(root.findall(f"{ACBFns}meta-data/{ACBFns}book-info/{ACBFns}author")):
	# 	print(i.tag)

	meta = root.findall(f"{ACBFns}meta-data/{ACBFns}book-info/{ACBFns}author")
	for i in meta:
		print(i.keys())
		# if i.find(f"{ACBFns}middle-name") is not None:
		# 	print(i.find(f"{ACBFns}middle-name").text)
		# if i.find(f"{ACBFns}last-name") is not None:
		# 	print(i.find(f"{ACBFns}last-name").text)
		# print(i.attrib["activity"].upper())
		# for j in list(i):
		# 	print(j.tag.replace(ACBFns, ""), ":", j.text)
	# info_iter = meta.iter()
	# while True:
	# 	try:
	# 		print(next(info_iter).tag)
	# 	except StopIteration:
	# 		break
