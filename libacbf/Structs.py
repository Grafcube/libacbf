from typing import AnyStr, Dict, List, Optional, Union
import libacbf.BodyInfo as body
from libacbf.Constants import AuthorActivities

class Author:
	"""
	docstring
	"""
	def __init__(self, first_name = None, last_name = None, nickname = None):
		self.first_name: Optional[AnyStr] = None
		self.last_name: Optional[AnyStr] = None
		self.nickname: Optional[AnyStr] = None

		if (first_name is not None and last_name is not None) or nickname is not None:
			self.first_name: Optional[AnyStr] = first_name
			self.last_name: Optional[AnyStr] = last_name
			self.nickname: Optional[AnyStr] = nickname
		else:
			raise ValueError("Author must have either First Name and Last Name or Nickname")

		self._activity: Optional[AnyStr] = None
		self.lang: Optional[AnyStr] = None
		self.middle_name: Optional[AnyStr] = None
		self.home_page: Optional[AnyStr] = None
		self.email: Optional[AnyStr] = None

	@property
	def activity(self) -> Optional[AuthorActivities]:
		return self._activity

	@activity.setter
	def activity(self, val: Union[AuthorActivities, int, AnyStr]):
		if type(val) is AuthorActivities:
			self._activity = val
		elif type(val) is str:
			self._activity = AuthorActivities[val]
		elif type(val) is int:
			self._activity = AuthorActivities(val)

class Genre:
	"""
	docstring
	"""
	def __init__(self):
		self.Genre: AnyStr = ""
		self.Match: Optional[int] = None

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
