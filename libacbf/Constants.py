from enum import Enum, auto

class BookNamespace:
	def __init__(self, ns: str):
		self.ACBFns = ns

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
	Adult = 0
	Adventure = auto()
	Alternative = auto()
	Biography = auto()
	Caricature = auto()
	Children = auto()
	Computer = auto()
	Crime = auto()
	Education = auto()
	Fantasy = auto()
	History = auto()
	Horror = auto()
	Humor = auto()
	Manga = auto()
	Military = auto()
	Mystery = auto()
	NonFiction = auto()
	Politics = auto()
	RealLife = auto()
	Religion = auto()
	Romance = auto()
	ScienceFiction = auto()
	Sports = auto()
	Superhero = auto()
	Western = auto()
	Other = 100

class TextAreas(Enum):
	Speech = 0
	Commentary = auto()
	Formal = auto()
	Letter = auto()
	Code = auto()
	Heading = auto()
	Audio = auto()
	Thought = auto()
	Sign = auto()

class PageTransitions(Enum):
	fade = 0
	blend = auto()
	scroll_right = auto()
	scroll_down = auto()
	none = 100
