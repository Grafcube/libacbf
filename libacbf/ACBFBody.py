from typing import List
from lxml import etree
from libacbf.ACBFBook import BookNamespace
from libacbf.BodyInfo import Page

class ACBFBody:
	"""
	docstring
	"""
	def __init__(self, body: etree._Element, ns: BookNamespace):
		self.pages: List[Page] = []
		page_items = body.findall(f"{ns.ACBFns}page")
		for pg in page_items:
			self.pages.append(Page(pg, ns))

		# Optional
		self.bgcolor: str = "#000000"
		if "bgcolor" in body.keys():
			self.bgcolor = body.attrib["bgcolor"]
