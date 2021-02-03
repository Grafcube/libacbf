import pathlib
from typing import Any, List, Dict, AnyStr
from re import sub, findall, IGNORECASE
from lxml import etree
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBody import ACBFBody

class ACBFBook:
	"""
	docstring
	"""
	def __init__(self, file_path):
		self.book_path = file_path

		self.tree = None
		self.root = None

		if pathlib.Path(file_path).suffix != ".acbf": # TODO cbz handling
			raise ValueError("File is not an ACBF Ebook")
		else:
			with open(file_path, encoding="utf-8") as book:
				contents = book.read()
				self.root = etree.fromstring(bytes(contents, encoding="utf-8"))
				self.tree = self.root.getroottree()

		self.namespace: AnyStr = r"{" + self.root.nsmap[None] + r"}"
		self.styles: List[AnyStr] = findall(r'<\?xml-stylesheet type="text\/css" href="(.+)"\?>', contents, IGNORECASE)

		self.Metadata: ACBFMetadata = ACBFMetadata(self.root.find(f"{self.namespace}meta-data"), self.namespace)

		self.Body: ACBFBody = ACBFBody(self.root.find(f"{self.namespace}body"), self.namespace)

		self.Stylesheet: AnyStr = self.root.find(f"{self.namespace}style").text.strip()

		self.References: Dict[AnyStr, Dict[AnyStr, AnyStr]] = get_references(self.root.find(f"{self.namespace}references"), self.namespace)

def get_references(ref_root, ACBFns) -> Dict[AnyStr, Dict[AnyStr, AnyStr]]:
		references = {}
		reference_items = ref_root.findall(f"{ACBFns}reference")
		for ref in reference_items:
			pa = []
			for p in ref.findall(f"{ACBFns}p"):
				text = sub(r"<\/?p[^>]*>", "", str(etree.tostring(p, encoding="utf-8"), encoding="utf-8").strip())
				pa.append(text)
			references[ref.attrib["id"]] = {"paragraph": "\n".join(pa)}
		return references
