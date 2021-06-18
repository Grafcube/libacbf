import os
import shutil
from pprint import pprint
from zipfile import ZipFile
import tarfile as tar
from pathlib import Path
from tempfile import TemporaryDirectory
from lxml import etree
# from libacbf import ACBFBook
from tests.testsettings import samples

# with ACBFBook(samples[1]) as book:
# 	for i in book.Body.pages:
# 		print(i.image_ref, len(i.image.data))

# with tar.open("tests/samples/more/test.tar.gz", 'w:gz') as arc:
# 	arc.add("tests/samples/more/cover.jpg", "cover.jpg")
# 	arc.add("tests/samples/more/JetBrainsMono[wght].ttf", "JetBrainsMono[wght].ttf")
# 	arc.list(False)

# Put this in save function
with TemporaryDirectory() as td:
	td = Path(td)
	with tar.open("tests/samples/more/test.tar.gz", 'r') as arc:
		arc.extractall(td)
	shutil.copy("tests/samples/more/cover.jpg", td/"copy.jpg")
	shutil.copy("tests/samples/more/JetBrainsMono[wght].ttf", td/"copy.ttf")
	os.makedirs(str(td/"more"), exist_ok=True)
	shutil.copy("tests/samples/more/JetBrainsMono[wght].ttf", td/"more/JetBrainsMono[wght].ttf")

	files = [x.relative_to(td) for x in td.rglob('*') if x.is_file()]

	with tar.open("tests/samples/more/test.tar.gz", 'w:gz') as arc:
		for i in files:
			arc.add(str(td/i), str(i))
		arc.list(False)

# ns = {None: "https://example.com/test/xml-schema.xsd"}

# root = etree.Element("root", nsmap=ns)

# element1 = etree.SubElement(root, "element1")
# element1.set("exists", "true")

# element2 = etree.SubElement(root, "element2")
# element2.set("something", "false")

# child1 = etree.SubElement(element2, "child1", {"index": "0"})
# child1.text = "something here."
# child2 = etree.SubElement(element2, "child2", {"index": "1"})
# child2.text = "Here's a newline."

# with open("tests/samples/more/test.xml", 'w', encoding="utf-8", newline='\n') as xml:
# 	xml.write(str(etree.tostring(root, encoding="utf-8", pretty_print=True), 'utf-8'))
