from typing import AnyStr, Dict, List, Optional, Union
from langcodes import Language, standardize_tag
import libacbf.BodyInfo as body
from libacbf.Constants import AuthorActivities, Genres

class Author:
	"""
	docstring
	"""
	def __init__(self, *names: AnyStr, first_name = None, last_name = None, nickname = None):
		self.first_name: Optional[AnyStr] = None
		self.last_name: Optional[AnyStr] = None
		self.nickname: Optional[AnyStr] = None

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
			self.first_name: Optional[AnyStr] = first_name
			self.last_name: Optional[AnyStr] = last_name
			self.nickname: Optional[AnyStr] = nickname
		else:
			raise ValueError("Author must have either First Name and Last Name or Nickname")

		self._activity: Optional[AuthorActivities] = None
		self._lang: Optional[Language] = None
		self.middle_name: Optional[AnyStr] = None
		self.home_page: Optional[AnyStr] = None
		self.email: Optional[AnyStr] = None

	@property
	def activity(self) -> Optional[AuthorActivities]:
		return self._activity

	@activity.setter
	def activity(self, val: Optional[Union[AuthorActivities, int, AnyStr]]):
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
	def lang(self, val: Optional[Union[AnyStr, Language]]):
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
	def __init__(self, gn: Union[AnyStr, Genres, int]):
		self.Genre: Genres = gn
		self.Match: Optional[int] = None

	@property
	def Genre(self) -> Genres:
		return self._genre

	@Genre.setter
	def Genre(self, gn: Union[AnyStr, Genres, int]):
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
	def __init__(self, href: AnyStr):
		self.image_ref: AnyStr = href
		self.text_layers: Dict[AnyStr, body.TextLayer] = {}
		self.frames: List[Frame] = []
		self.jumps: List[Jump] = []

class LanguageLayer:
	"""
	docstring
	"""
	def __init__(self):
		self.lang: AnyStr = ""
		self.show: Optional[bool] = None

class Series:
	"""
	docstring
	"""
	def __init__(self):
		self.title: AnyStr = ""
		self.sequence: AnyStr = ""
		self.lang: Optional[AnyStr] = None
		self.volume: Optional[AnyStr] = None

class DBRef:
	"""
	docstring
	"""
	def __init__(self):
		self.dbname: AnyStr = ""
		self.text: AnyStr = ""
		self.type: Optional[AnyStr] = None

class Frame:
	"""
	docstring
	"""
	def __init__(self):
		self.points: List = []
		self.bgcolor: Optional[AnyStr] = None

class Jump:
	"""
	docstring
	"""
	def __init__(self):
		self.page: Optional[int] = None
		self.points: List = []
