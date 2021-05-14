from __future__ import annotations
from typing import List, TYPE_CHECKING, Dict, Optional
if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from libacbf.Constants import BookNamespace
from libacbf.BodyInfo import Page

class ACBFBody:
	"""Body section contains the definition of individual book pages, text layers, frames and jumps
	inside those pages.

	See Also
	--------
	`Body Section Definition <https://acbf.fandom.com/wiki/Body_Section_Definition>`_.

	Attributes
	----------
	book : ACBFBook
		Book that this body section belongs to.

	pages : List[libacbf.BodyInfo.Page]
		A list of :class:`Page <libacbf.BodyInfo.Page>` objects in order.

	bgcolor : str, optional
		Defines a background colour for the whole book. Can be overridden by ``bgcolor`` in pages,
		text layers and text areas.
	"""
	def __init__(self, book: ACBFBook):
		self.book = book

		ns = book.namespace
		body = book._root.find(f"{ns.ACBFns}body")
		page_items = body.findall(f"{ns.ACBFns}page")

		pgs = []
		for pg in page_items:
			pgs.append(Page(pg, book))

		self.pages: List[Page] = pgs

		# Optional
		self.bgcolor: Optional[str] = None
		if "bgcolor" in body.keys():
			self.bgcolor = body.attrib["bgcolor"]
