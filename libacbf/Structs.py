from typing import AnyStr, Dict, List, Optional
import libacbf.BodyInfo as body

class Author:
	"""
	docstring
	"""
	def __init__(self):
		self.activity: Optional[AnyStr] = None
		self.lang: Optional[AnyStr] = None
		self.first_name: Optional[AnyStr] = None
		self.last_name: Optional[AnyStr] = None
		self.middle_name: Optional[AnyStr] = None
		self.nickname: Optional[AnyStr] = None
		self.home_page: Optional[AnyStr] = None
		self.email: Optional[AnyStr] = None

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
	def __init__(self):
		self.image_ref: AnyStr = ""
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
