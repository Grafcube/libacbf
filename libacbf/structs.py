from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional, Union
from pathlib import Path
import re
import langcodes

if TYPE_CHECKING:
	from libacbf import ACBFBook
from libacbf.constants import AuthorActivities, Genres
import libacbf.helpers as helpers

class Styles:
	def __init__(self, book: ACBFBook, contents: str):
		self.book = book
		self._contents = contents

		self.styles: Dict[str, Optional[str]] = {}
		self.sync_styles()

	def list_styles(self) -> List[str]:
		return [str(x) for x in self.styles.keys()]

	def sync_styles(self):
		self.styles.clear()
		style_refs = re.findall(r'<\?xml-stylesheet type="text/css" href="(.+)"\?>', self._contents, re.IGNORECASE)
		for i in style_refs:
			self.styles[i] = None

		if self.book._root.find(f"{self.book._namespace}style") is not None:
			self.styles['_'] = None

	@helpers.check_book
	def edit_style(self, stylesheet_ref: Union[str, Path], style_name: Optional[str] = None, embed: bool = False):
		if isinstance(stylesheet_ref, str):
			stylesheet_ref = Path(stylesheet_ref)

		if style_name is None and not embed:
			style_name = stylesheet_ref.name

		if embed:
			pass
		else:
			self.book.archive.write(stylesheet_ref, style_name)


	@helpers.check_book
	def remove_style(self, style_name: str = '_'): # TODO
		self.sync_styles()

	def __len__(self):
		len(self.styles.keys())

	def __getitem__(self, key: str):
		if key in self.styles.keys():
			if self.styles[key] is not None:
				return self.styles[key]
			elif key == '_':
				self.styles['_'] = self.book._root.find(f"{self.book._namespace}style").text.strip()
			else:
				if self.book.archive is None:
					st_path = self.book.book_path.parent / Path(key)
					with open(str(st_path), 'r') as st:
						self.styles[key] = st.read()
				else:
					self.styles[key] = self.book.archive.read(key).decode("utf-8")
			return self.styles[key]
		else:
			raise FileNotFoundError

class Author:
	"""Defines an author of the comic book.

	See Also
	--------
	`Body Info Author specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Author>`_.

	Examples
	--------
	An ``Author`` object can be created with either a nickname, a first and last name or both. ::

		from libacbf.structs import Author

		author1 = Author("Hugh", "Mann")
		# author1.first_name == "Hugh"
		# author1.last_name == "Mann"

		author2 = Author("NotAPlatypus")
		# author2.nickname == "NotAPlatypus"

		author3 = Author("Hugh", "Mann", "NotAPlatypus")
		# author3.first_name == "Hugh"
		# author3.last_name == "Mann"
		# author3.nickname == "NotAPlatypus"

	This is also possible::

		author4 = Author(first_name="Hugh", last_name="Mann", nickname="NotAPlatypus")

	Attributes
	----------
	first_name : str
		Author's first name.

	last_name : str
		Author's last name.

	nickname : str
		Author's nickname.

	middle_name : str, optional
		Author's middle name.

	home_page : str, optional
		Author's website.

	email : str, optional
		Author's email address.
	"""
	def __init__(self, *names: str, first_name=None, last_name=None, nickname=None):
		self._element = None

		self._first_name: Optional[str] = None
		self._last_name: Optional[str] = None
		self.nickname: Optional[str] = None

		if len(names) == 1:
			nickname = names[0]
		elif len(names) == 2:
			first_name = names[0]
			last_name = names[1]
		elif len(names) >= 3:
			first_name = names[0]
			last_name = names[1]
			nickname = names[2]

		if (first_name is not None and last_name is not None) or nickname is not None:
			self._first_name: Optional[str] = first_name
			self._last_name: Optional[str] = last_name
			self.nickname: Optional[str] = nickname
		else:
			raise ValueError("Author must have either First Name and Last Name or Nickname.")

		self._activity: Optional[AuthorActivities] = None
		self._lang: Optional[str] = None
		self.middle_name: Optional[str] = None
		self.home_page: Optional[str] = None
		self.email: Optional[str] = None

	@property
	def first_name(self) -> str:
		return self._first_name

	@first_name.setter
	def first_name(self, val: str):
		if self.last_name is not None or self.nickname is not None:
			self._first_name = val
		else:
			raise ValueError("Author must have either First Name and Last Name or Nickname.")

	@property
	def last_name(self) -> str:
		return self._last_name

	@last_name.setter
	def last_name(self, val: str):
		if self.first_name is not None or self.nickname is not None:
			self._last_name = val
		else:
			raise ValueError("Author must have either First Name and Last Name or Nickname.")

	@property
	def activity(self) -> Optional[AuthorActivities]:
		"""Defines the activity that a particular author carried out on the comic book.

		Allowed values are defined in :class:`AuthorActivities <libacbf.constants.AuthorActivities>`.

		Returns
		-------
		Optional[AuthorActivities]
			A value from :class:`AuthorActivities <libacbf.constants.AuthorActivities>` Enum.
		"""
		return self._activity

	@activity.setter
	def activity(self, val: Optional[Union[AuthorActivities, int, str]]):
		if val is None:
			self._activity = None
		elif type(val) is AuthorActivities:
			self._activity = val
		elif type(val) is str:
			self._activity = AuthorActivities[val]
		elif type(val) is int:
			self._activity = AuthorActivities(val)
		else:
			raise ValueError("`Author.activity` must be an `int`, `str` or `constants.AuthorActivities`.")

	@property
	def lang(self) -> Optional[str]:
		"""Defines the language that the author worked in.

		Returns
		-------
		Optional[str]
			Returns a standard language code.
		"""
		return self._lang

	@lang.setter
	def lang(self, val: Optional[str]):
		if val is None:
			self._lang = None
		else:
			self._lang = langcodes.standardize_tag(val)

	def copy(self) -> Author:
		"""Creates a copy of this ``Author`` object not connected to any book.

		Returns
		-------
		Author
			Copy of this object.
		"""
		copy = Author(self.first_name, self.last_name, self.nickname)
		copy.activity = self.activity
		copy.lang = self.lang
		copy.middle_name = self.middle_name
		copy.home_page = self.home_page
		copy.email = self.email
		return copy

class Genre:
	"""The genre of the book.

	See Also
	--------
	`Body Info genre specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Genre>`_.

	Parameters
	----------
	genre_type : Genres(Enum) | str | int
		The genre value. String and integer are converted to a value from
		:class:`Genres <libacbf.constants.Genres>` Enum.

	match : int, optional
		The match value. Must be an integer from 0 to 100.
	"""
	def __init__(self, genre_type: Union[str, Genres, int], match: Optional[int] = None):
		self.genre: Genres = genre_type
		self.match: Optional[int] = match

	@property
	def genre(self) -> Genres:
		"""Defines the activity that a particular author carried out on the comic book.

		Allowed values are defined in :class:`Genres <libacbf.constants.Genres>`.

		Returns
		-------
		Optional[Genres]
			A value from :class:`Genres <libacbf.constants.Genres>` Enum.
		"""
		return self._genre

	@genre.setter
	def genre(self, gn: Union[str, Genres, int]):
		if type(gn) is Genres:
			self._genre = gn
		elif type(gn) is str:
			self._genre = Genres[gn]
		elif type(gn) is int:
			self._genre = Genres(gn)

	@property
	def match(self) -> Optional[int]:
		"""Defines the match percentage to that particular genre.

		Returns
		-------
		Optional[int]
			An integer percentage from 0 to 100.
		"""
		return self._match

	@match.setter
	def match(self, val: Optional[int] = None):
		self._match = None
		if val is not None:
			if 0 <= val <= 100:
				self._match = val
			else:
				raise ValueError("match must be an int from 0 to 100.")

class LanguageLayer:
	"""Used by :attr:`BookInfo.languages <libacbf.metadata.BookInfo.languages>`.

	See Also
	--------
	`Body Info Languages specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Languages>`_.

	Attributes
	----------
	lang : str
		Language of layer as a standard language code.

	show : bool
		Whether layer is drawn.
	"""

	def __init__(self, val: str, show: bool):
		self._element = None

		self.lang: str = langcodes.standardize_tag(val)
		self.show: bool = show

class Series:
	"""Used by :attr:`BookInfo.series <libacbf.metadata.BookInfo.series>`.

	See Also
	--------
	`Body Info Sequence specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Sequence>`_.

	Attributes
	----------
	title : str
		Title of the series that this book is part of.

	sequence : str
		The book's position/entry in the series.

	volume : str, optional
		The volume that the book belongs to.
	"""

	def __init__(self, title: str, sequence: str, volume: Optional[str] = None):
		self.title: str = title
		self.sequence: str = sequence
		self.volume: Optional[str] = volume

class DBRef:
	"""Used by :attr:`BookInfo.database_ref <libacbf.metadata.BookInfo.database_ref>`.

	See Also
	--------
	`Book Info DatabaseRef specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#DatabaseRef>`_.

	Attributes
	----------
	dbname : str
		Name of database.

	reference : str
		Reference of book in database.

	type : str, optional
		Type of the given reference such as URL, ID etc.
	"""

	def __init__(self, dbname: str, ref: str):
		self._element = None

		self.dbname: str = dbname
		self.reference: str = ref
		self.type: Optional[str] = None

class Frame:
	"""A subsection of a page.

	See Also
	--------
	`Body Info Frame specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Frame>`_.

	Attributes
	----------
	points : List[2D Vectors]
		A list of named tuples with ``x`` and ``y`` values representing a 2-dimensional vector. ::

			sixth_point = frame.points[5]
			sixth_point.x # x-coordinate of point
			sixth_point.y # y-coordinate of point

	bgcolor : str, optional
		Defines the background colour for the page. Inherits from :attr:`Page.bgcolor <libacbf.body.Page.bgcolor>`
		if ``None``.
	"""

	def __init__(self, points: List[helpers.Vec2]):
		self._element = None

		self.points: List[helpers.Vec2] = points
		self.bgcolor: Optional[str] = None

	@helpers.check_book
	def set_point(self, idx: int, x: int, y: int):
		self.points[idx] = helpers.Vec2(x, y)
		self._element.set("points", helpers.vec_to_pts(self.points))

	@helpers.check_book
	def remove_point(self, idx: int):
		if len(self.points) == 1:
			raise ValueError("`points` cannot be empty.")
		self.points.pop(idx)
		self._element.set("points", helpers.vec_to_pts(self.points))

	@helpers.check_book
	def set_bgcolor(self, bg: Optional[str]):
		if bg is not None:
			self._element.set("bgcolor", bg)
		elif "bgcolor" in self._element.attrib:
			self._element.attrib.pop("bgcolor")
		self.bgcolor = bg

class Jump:
	"""Clickable area on a page which navigates to another page.

	See Also
	--------
	`Body Info Jump specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Jump>`_.

	Attributes
	----------
	points : List[2D Vectors]
		A list of named tuples with ``x`` and ``y`` values representing a 2-dimensional vector. Same
		as :attr:`Frame.points`.

	page : int
		Target page to go to when clicked. Pages start from 1 so first page is ``1``, second page is
		``2`` and so on.
	"""

	def __init__(self, points: List[helpers.Vec2], page: int):
		self._element = None

		self.page: int = page
		self.points: List[helpers.Vec2] = points

	@helpers.check_book
	def set_target_page(self, target_page: int):
		self._element.set("page", str(target_page))
		self.page = target_page

	@helpers.check_book
	def set_point(self, idx: int, x: int, y: int):
		self.points[idx] = helpers.Vec2(x, y)
		self._element.set("points", helpers.vec_to_pts(self.points))

	@helpers.check_book
	def remove_point(self, idx: int):
		if len(self.points) == 1:
			raise ValueError("`points` cannot be empty.")
		self.points.pop(idx)
		self._element.set("points", helpers.vec_to_pts(self.points))
