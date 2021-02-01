from enum import Enum

class AuthorActivities(Enum):
	"""
	docstring
	"""
	Writer = 0
	Adapter = 1
	Artist = 2
	Penciller = 3
	Inker = 4
	Colorist = 5
	Letterer = 6
	CoverArtist = 7
	Photographer = 8
	Editor = 9
	AssistantEditor = 10
	Translator = 11
	Other = 100

class Genres(Enum):
	"""
	docstring
	"""
	Adult = 0
	Adventure = 1
	Alternative = 2
	Biography = 3
	Caricature = 4
	Children = 5
	Computer = 6
	Crime = 7
	Education = 8
	Fantasy = 9
	History = 10
	Horror = 11
	Humor = 12
	Manga = 13
	Military = 14
	Mystery = 15
	NonFiction = 16
	Politics = 17
	RealLife = 18
	Religion = 19
	Romance = 20
	ScienceFiction = 21
	Sports = 22
	Superhero = 23
	Western = 24
	Other = 100

class TextAreas(Enum):
	Speech = 0
	Commentary = 1
	Formal = 2
	Letter = 3
	Code = 4
	Heading = 5
	Audio = 6
	Thought = 7
	Sign = 8

class PageTransitions(Enum):
	fade = 0
	blend = 1
	scroll_right = 2
	scroll_down = 3
	none = 100
