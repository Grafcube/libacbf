from typing import List
from lxml import etree
from libacbf.BodyInfo import Page

class ACBFBody:
	"""
	docstring
	"""
	def __init__(self, body: etree._Element, ACBFns: str):
		self.pages: List[Page] = []
		page_items = body.findall(f"{ACBFns}page")
		for pg in page_items:
			self.pages.append(Page(pg, ACBFns))

		# Optional
		self.bgcolor: str = "#000000"
		if "bgcolor" in body.keys():
			self.bgcolor = body.attrib["bgcolor"]
