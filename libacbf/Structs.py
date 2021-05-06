from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional, Union
if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from pathlib import Path
from langcodes import Language, standardize_tag
import libacbf.BodyInfo as body
from libacbf.Constants import AuthorActivities, Genres

class Styles:
	"""
	docstring
	"""
	def __init__(self, book: ACBFBook, style_refs: List[str]):
		self.book = book

		self.styles: Dict[str, Optional[str]] = {}
		for i in style_refs:
			self.styles[i] = None

	def list_styles(self) -> List[str]:
		fl = []
		for i in self.styles.keys():
			fl.append(str(i))
		return fl

	def __len__(self):
		len(self.styles.keys())

	def __getitem__(self, key: str):
		if key in self.styles.keys():
			if self.styles[key] is not None:
				return self.styles[key]
			else:
				if self.book.archive is None:
					st_path = self.book.file_path.parent/Path(key)
					with open(str(st_path), 'r', encoding="utf-8") as st:
						self.styles[key] = st.read()
				else:
					with self.book.archive.open(key, 'r') as st:
						self.styles[key] = str(st.read(), "utf-8")
			return self.styles[key]
		else:
			raise FileNotFoundError

class Author:
	"""
	docstring
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
		self._lang: Optional[Language] = None
		self.middle_name: Optional[str] = None
		self.home_page: Optional[str] = None
		self.email: Optional[str] = None

	@property
	def activity(self) -> Optional[AuthorActivities]:
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
	def lang(self) -> Optional[Language]:
		return self._lang

	@lang.setter
	def lang(self, val: Optional[Union[str, Language]]):
		if val is None:
			self._lang = None
		elif type(val) is Language:
			self._lang = val
		elif type(val) is str:
			self._lang = Language.get(standardize_tag(val))

class Genre:
	"""
	docstring
	"""
	def __init__(self, genre_type: Union[str, Genres, int], match: Optional[int] = None):
		self.Genre: Genres = genre_type
		self.Match: Optional[int] = match

	@property
	def Genre(self) -> Genres:
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
		return self._match

	@Match.setter
	def Match(self, val: Optional[int] = None):
		self._match = None
		if val is not None:
			if val >= 0 and val <= 100:
				self._match = val
			else:
				raise ValueError("Match must be an int from 0 to 100.")

class CoverPage:
	"""
	docstring
	"""
	def __init__(self, href: str):
		self.image_ref: str = href
		self.text_layers: Dict[str, body.TextLayer] = {}
		self.frames: List[Frame] = []
		self.jumps: List[Jump] = []

class LanguageLayer:
	"""
	docstring
	"""
	def __init__(self):
		self.lang: str = ""
		self.show: Optional[bool] = None

class Series:
	"""
	docstring
	"""
	def __init__(self):
		self.title: str = ""
		self.sequence: str = ""
		self.lang: Optional[str] = None
		self.volume: Optional[str] = None

class DBRef:
	"""
	docstring
	"""
	def __init__(self):
		self.dbname: str = ""
		self.text: str = ""
		self.type: Optional[str] = None

class Frame:
	"""
	docstring
	"""
	def __init__(self):
		self.points: List[body.Vec2] = []
		self.bgcolor: Optional[str] = None

class Jump:
	"""
	docstring
	"""
	def __init__(self):
		self.page: Optional[int] = None
		self.points: List[body.Vec2] = []
