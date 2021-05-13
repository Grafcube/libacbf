from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional
if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from libacbf.Constants import BookNamespace
from libacbf.BodyInfo import Page

class ACBFBody:
	"""[summary]
	"""
	def __init__(self, book: ACBFBook):
		self.book = book

		self._ns: BookNamespace = book.namespace
		self._body = book._root.find(f"{self._ns.ACBFns}body")
		self._first_page = self._body.find(f"{self._ns.ACBFns}page")
		self._current_page = self._first_page

		self.pages: Dict[int, Page] = {}
		self.page: Optional[Page] = self[0]
		self.page_index: Optional[int] = 0

		# Optional
		self.bgcolor: str = "#000000"
		if "bgcolor" in self._body.keys():
			self.bgcolor = self._body.attrib["bgcolor"]

	@property
	def total_pages(self) -> int:
		"""[summary]
		"""
		return len(list(self._body))

	def __len__(self):
		return self.total_pages

	def __getitem__(self, index: int):
		self.page_index = index
		if self.page_index in self.pages.keys():
			self.page = self.pages[self.page_index]
			return self.page
		else:
			self._current_page = self._body.findall(f"{self._ns.ACBFns}page")[index]
			self.page = Page(self._current_page, self.book)
			self.pages[self.page_index] = self.page
			return self.page

	def __iter__(self):
		self.page = None
		self.page_index = None
		self._current_page = self._first_page
		return self

	def __next__(self):
		pg = self.next_page()
		if pg is not None:
			return pg
		else:
			raise StopIteration

	def next_page(self):
		"""[summary]

		Returns
		-------
		[type]
			[description]
		"""
		if self.page_index is not None:
			self.page_index += 1
		else:
			self.page_index = 0

		if self.page_index in self.pages.keys():
			self.page = self.pages[self.page_index]
			return self.page
		else:
			if self.page_index != 0:
				self._current_page = self._current_page.getnext()
			if self._current_page is None:
				self.page = None
			else:
				self.page = Page(self._current_page, self.book)
				self.pages[self.page_index] = self.page
		return self.page

	def previous_page(self):
		"""[summary]

		Returns
		-------
		[type]
			[description]

		Raises
		------
		StopIteration
			[description]
		"""
		self.page_index -= 1
		if self.page_index in self.pages.keys():
			self.page = self.pages[self.page_index]
			return self.page
		else:
			self._current_page = self._current_page.getprevious()
			if self._current_page is not None:
				self.page = Page(self._current_page, self.book)
				self.pages[self.page_index] = self.page
				return self.page
			else:
				self.page = None
				self.page_index = 0
				raise StopIteration
