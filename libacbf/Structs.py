from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional, Union
from collections import namedtuple
from pathlib import Path
import re
import langcodes

if TYPE_CHECKING:
	from libacbf import ACBFBook
from libacbf.constants import AuthorActivities, Genres

Vec2 = namedtuple("Vector2", "x y")

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
		style_refs = re.findall(r'<\?xml-stylesheet type="text\/css" href="(.+)"\?>', self._contents, re.IGNORECASE)
		for i in style_refs:
			self.styles[i] = None

		if self.book._root.find(f"{self.book.namespace.ACBFns}style") is not None:
			self.styles["_"] = None

	def __len__(self):
		len(self.styles.keys())

	def __getitem__(self, key: str):
		if key in self.styles.keys():
			if self.styles[key] is not None:
				return self.styles[key]
			elif key == "_":
				self.styles["_"] = self.book._root.find(f"{self.book.namespace.ACBFns}style").text.strip()
			else:
				if self.book.archive is None:
					st_path = self.book.book_path.parent/Path(key)
					with open(str(st_path), 'r', encoding="utf-8") as st:
						self.styles[key] = st.read()
				else:
					self.styles[key] = str(self.book.archive.read(key), "utf-8")
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
	def __init__(self, *names: str, first_name = None, last_name = None, nickname = None):
		self._element = None

		self.first_name: Optional[str] = None
		self.last_name: Optional[str] = None
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
			self.first_name: Optional[str] = first_name
			self.last_name: Optional[str] = last_name
			self.nickname: Optional[str] = nickname
		else:
			raise ValueError("Author must have either First Name and Last Name or Nickname.")

		self._activity: Optional[AuthorActivities] = None
		self._lang: Optional[str] = None
		self.middle_name: Optional[str] = None
		self.home_page: Optional[str] = None
		self.email: Optional[str] = None

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

class Genre:
	"""The genre of the book.

	See Also
	--------
	`Body Info Genre specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Genre>`_.

	Parameters
	----------
	genre_type : Genres(Enum) | str | int
		The genre value. String and integer are converted to a value from
		:class:`Genres <libacbf.constants.Genres>` Enum.

	match : int, optional
		The match value. Must be an integer from 0 to 100.
	"""
	def __init__(self, genre_type: Union[str, Genres, int], match: Optional[int] = None):
		self.Genre: Genres = genre_type
		self.Match: Optional[int] = match

	@property
	def Genre(self) -> Genres:
		"""Defines the activity that a particular author carried out on the comic book.

		Allowed values are defined in :class:`Genres <libacbf.constants.Genres>`.

		Returns
		-------
		Optional[Genres]
			A value from :class:`Genres <libacbf.constants.Genres>` Enum.
		"""
		return self._genre

	@Genre.setter
	def Genre(self, gn: Union[str, Genres, int]):
		if type(gn) is Genres:
			self._genre = gn
		elif type(gn) is str:
			self._genre = Genres[gn]
		elif type(gn) is int:
			self._genre = Genres(gn)

	@property
	def Match(self) -> Optional[int]:
		"""Defines the match percentage to that particular genre.

		Returns
		-------
		Optional[int]
			An integer percentage from 0 to 100.
		"""
		return self._match

	@Match.setter
	def Match(self, val: Optional[int] = None):
		self._match = None
		if val is not None:
			if val >= 0 and val <= 100:
				self._match = val
			else:
				raise ValueError("Match must be an int from 0 to 100.")

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
	def __init__(self, points: List[Vec2]):
		self.points: List[Vec2] = points
		self.bgcolor: Optional[str] = None

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
	def __init__(self, points: List[Vec2], page: int):
		self.points: List[Vec2] = points
		self.page: int = page
