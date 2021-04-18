from typing import Dict, List, Optional, Union
from langcodes import Language, standardize_tag
import libacbf.BodyInfo as body
from libacbf.Constants import AuthorActivities, Genres

class Author:
	"""
	docstring
	"""
	def __init__(self, *names: str, first_name = None, last_name = None, nickname = None):
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
			raise ValueError("Author must have either First Name and Last Name or Nickname")

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
	def __init__(self, gn: Union[str, Genres, int]):
		self.Genre: Genres = gn
		self.Match: Optional[int] = None

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
		self.points: List = []
		self.bgcolor: Optional[str] = None

class Jump:
	"""
	docstring
	"""
	def __init__(self):
		self.page: Optional[int] = None
		self.points: List = []
