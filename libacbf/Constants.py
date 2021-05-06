from enum import Enum, auto
from re import sub

class BookNamespace:
	def __init__(self, ns: str):
		self.ACBFns: str = ns

	@property
	def ACBFns_raw(self) -> str:
		return sub(r'\{|\}', "", self.ACBFns)

class AuthorActivities(Enum):
	"""
	docstring
	"""
	Writer = 0
	Adapter = auto()
	Artist = auto()
	Penciller = auto()
	Inker = auto()
	Colorist = auto()
	Letterer = auto()
	CoverArtist = auto()
	Photographer = auto()
	Editor = auto()
	AssistantEditor = auto()
	Translator = auto()
	Other = 100

class Genres(Enum):
	"""
	docstring
	"""
	adult = 0
	adventure = auto()
	alternative = auto()
	biography = auto()
	caricature = auto()
	children = auto()
	computer = auto()
	crime = auto()
	education = auto()
	fantasy = auto()
	history = auto()
	horror = auto()
	humor = auto()
	manga = auto()
	military = auto()
	mystery = auto()
	non_fiction = auto()
	politics = auto()
	real_life = auto()
	religion = auto()
	romance = auto()
	science_fiction = auto()
	sports = auto()
	superhero = auto()
	western = auto()
	other = 100

class TextAreas(Enum):
	speech = 0
	commentary = auto()
	formal = auto()
	letter = auto()
	code = auto()
	heading = auto()
	audio = auto()
	thought = auto()
	sign = auto()

class PageTransitions(Enum):
	fade = 0
	blend = auto()
	scroll_right = auto()
	scroll_down = auto()
	none = 100

class ImageRefType(Enum):
	"""
	docstring
	"""
	Embedded = 0
	Archived = auto()
	SelfArchived = auto()
	URL = auto()
	Local = auto()
