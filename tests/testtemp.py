from pprint import pprint
# from libacbf import ACBFBook
from lxml import etree
import tests.testres as res

# with ACBFBook(res.samples["cbz"]) as book:
# 	pprint([x.__dict__ for x in book.Metadata.book_info.authors])

root = etree.Element("root")
child0 = etree.SubElement(root, "child0")
child1 = etree.SubElement(root, "child1")
child2 = etree.SubElement(root, "child2")
grandchild0 = etree.SubElement(child2, "grandchild0")
grandchild1 = etree.SubElement(child2, "grandchild1")
child3 = etree.SubElement(root, "child3")

for i in root.iter():
	print(i.tag)

pprint([x for x in root.iter() if x != root])

pprint(etree.tostring(root, pretty_print=True).decode("utf-8"))

root.remove(child2)
root.insert(0, child2)

pprint(etree.tostring(root, pretty_print=True).decode("utf-8"))
