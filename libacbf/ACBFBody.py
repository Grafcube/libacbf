from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional
if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from libacbf.Constants import BookNamespace
from libacbf.BodyInfo import Page

class ACBFBody:
	"""
	docstring
	"""
	def __init__(self, book: ACBFBook):
		self.book = book

		self._ns: BookNamespace = book.namespace
		self._body = book.root.find(f"{self._ns.ACBFns}body")
		self._first_page = self._body.find(f"{self._ns.ACBFns}page")
		self._current_page = self._first_page

		self.page: Optional[Page] = None
		self.total_pages: int = len(list(self._body))
		self.pages: Dict[int, Page] = {}
		self.page_number: int = 0

		# Optional
		self.bgcolor: str = "#000000"
		if "bgcolor" in self._body.keys():
			self.bgcolor = self._body.attrib["bgcolor"]

	def __len__(self):
		return self.total_pages

	def __getitem__(self, index: int):
		self.page_number = index + 1
		if self.page_number in self.pages.keys():
			self.page = self.pages[self.page_number]
			return self.page
		else:
			self._current_page = self._body.findall(f"{self._ns.ACBFns}page")[index]
			self.page = Page(self._current_page, self.book)
			self.pages[self.page_number] = self.page
			return self.page

	def __iter__(self):
		self.page = None
		self.page_number = 0
		self._first_page = self._body.find(f"{self._ns.ACBFns}page")
		self._current_page = self._first_page
		return self

	def __next__(self):
		pg = self.next_page()
		if pg is not None:
			return pg
		else:
			raise StopIteration

	def next_page(self):
		self.page_number += 1
		if self.page_number in self.pages.keys():
			self.page = self.pages[self.page_number]
			return self.page
		else:
			self._current_page = self._current_page.getnext()
			if self._current_page is not None:
				self.page = Page(self._current_page, self.book)
				self.pages[self.page_number] = self.page
			else:
				self.page = None
				self.page_number = 0
		return self.page

	def previous_page(self):
		self.page_number -= 1
		if self.page_number in self.pages.keys():
			self.page = self.pages[self.page_number]
			return self.page
		else:
			self._current_page = self._current_page.getprevious()
			if self._current_page is not None:
				self.page = Page(self._current_page, self.book)
				self.pages[self.page_number] = self.page
				return self.page
			else:
				self.page = None
				self.page_number = 0
				raise StopIteration
