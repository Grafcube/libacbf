from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional
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

	Examples
	--------
	``ACBFBody[page index]`` can be used to get a specific page as a :class:`Page <libacbf.BodyInfo.Page>`
	object. ::

		from libacbf.ACBFBook import ACBFBook

		book = ACBFBook("path/to/book.cbz)

		page_no_42 = book.Body[41]

	``ACBFBody`` can also be used as an iterator. ::

		from libacbf.ACBFBook import ACBFBook

		book = ACBFBook("path/to/book.cbz)

		body_iter = iter(book.Body)

		page_no_0 = next(body_iter)
		# Returns first page

		page_no_1 = next(body_iter)
		# Returns second page

	Getting a specific page *after* creating the iterator changes where it continues. ::

		pg5 = book.Body[4]
		# Returns fifth page

		body_iter = iter(book.Body)

		page = next(body_iter)
		# Returns first page

		page_no_9 = book.Body[8]
		# Get ninth page

		next_page = next(body_iter)
		# Returns tenth page

	To get all pages as a list::

		from libacbf.ACBFBook import ACBFBook

		book = ACBFBook("path/to/book.cbz)

		body_list = list(iter(book.Body))
		# List of all pages

	Attributes
	----------
	book : ACBFBook
		Book that this body section belongs to.

	bgcolor : str, optional
		Defines a background colour for the whole book. Can be overridden by ``bgcolor`` in pages,
		text layers and text areas.

	page : libacbf.BodyInfo.Page, optional
		The page that the iterator is currently on. It is ``None`` if the iterator was just created
		or if :func:`reset_iterator()` was just called.

	page_index : int, optional
		The index of the page that the iterator is currently on. It is ``None`` if the iterator was
		just created or if :meth:`reset_iterator()` was just called.
	"""
	def __init__(self, book: ACBFBook):
		self.book = book

		self._ns: BookNamespace = book.namespace
		self._body = book._root.find(f"{self._ns.ACBFns}body")
		self._first_page = self._body.find(f"{self._ns.ACBFns}page")
		self._current_page = self._first_page

		self._pages: Dict[int, Page] = {}
		self.page: Optional[Page] = None
		self.page_index: Optional[int] = None

		# Optional
		self.bgcolor: Optional[str] = None
		if "bgcolor" in self._body.keys():
			self.bgcolor = self._body.attrib["bgcolor"]

	@property
	def total_pages(self) -> int:
		"""The total number of pages in the book.

		Returns
		-------
		int
			Returns an integer value.
		"""
		return len(list(self._body))

	def next_page(self):
		if self.page_index is not None:
			self.page_index += 1
		else:
			self.page_index = 0

		if self.page_index in self._pages.keys():
			self.page = self._pages[self.page_index]
			return self.page
		else:
			if self.page_index != 0:
				self._current_page = self._current_page.getnext()
			if self._current_page is None:
				self.page = None
			else:
				self.page = Page(self._current_page, self.book)
				self._pages[self.page_index] = self.page
		return self.page

	def previous_page(self):
		"""Get the previous page when iterating.

		Examples
		--------
		Can be used while iterating::

			from libacbf.ACBFBook import ACBFBook

			book = ACBFBook("path/to/book.cbz")

			body_iter = iter(book.Body)
			page_0 = next(body_iter)
			page_1 = next(body_iter)
			...
			page_19 = next(body_iter)
			page_20 = next(body_iter)

			page_19_back = book.Body.previous_page()
			# page_19 == page_19_back

		Returns
		-------
		libacbf.BodyInfo.Page
			Returns a :class:`Page <libacbf.BodyInfo.Page>` object.

		Raises
		------
		StopIteration
			Raised when the function is called when :attr:`page_index` == 0.
		"""
		self.page_index -= 1
		if self.page_index in self._pages.keys():
			self.page = self._pages[self.page_index]
			return self.page
		else:
			self._current_page = self._current_page.getprevious()
			if self._current_page is not None:
				self.page = Page(self._current_page, self.book)
				self._pages[self.page_index] = self.page
				return self.page
			else:
				self.page = None
				self.page_index = 0
				raise StopIteration

	def reset_iterator(self):
		"""Reset the iterator to the beginning.

		Examples
		--------
		If you want to start iterating from the first page after using ``next()`` and ``previous_page()``
		a few times::

			from libacbf.ACBFBook import ACBFBook

			book = ACBFBook("path/to/book.cbz")

			body_iter = iter(book.Body)
			page = next(body_iter)
			page = next(body_iter)
			page = book.Body.previous_page()
			page = next(body_iter)
			...
			page = book.Body.previous_page()
			page = next(body_iter)
			# Returns some page

			book.Body.reset_iterator()
			page = next(body_iter)
			# Returns the first page
		"""
		self.page = None
		self.page_index = None
		self._current_page = self._first_page

	def __len__(self):
		return self.total_pages

	def __getitem__(self, index: int):
		self.page_index = index
		if self.page_index in self._pages.keys():
			self.page = self._pages[self.page_index]
			return self.page
		else:
			self._current_page = self._body.findall(f"{self._ns.ACBFns}page")[index]
			self.page = Page(self._current_page, self.book)
			self._pages[self.page_index] = self.page
			return self.page

	def __iter__(self):
		self.reset_iterator()
		return self

	def __next__(self):
		pg = self.next_page()
		if pg is not None:
			return pg
		else:
			raise StopIteration
