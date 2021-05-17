import re
from enum import Enum, auto

class BookNamespace:
	def __init__(self, ns: str):
		self.ACBFns: str = ns

	@property
	def ACBFns_raw(self) -> str:
		return re.sub(r'\{|\}', "", self.ACBFns)

class AuthorActivities(Enum):
	"""List of accepted values for :attr:`Author.activity<libacbf.structs.Author.activity>`.

	See Also
	--------
	`ACBF Author specification <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Author>`_.
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
	"""List of accepted values for :attr:`Genre.Genre <libacbf.structs.Genre.Genre>`.

	See Also
	--------
	`ACBF Genre specification <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Genre>`_
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
	"""Types of text areas. Used by :attr:`TextArea.type <libacbf.body.TextArea.type>`.

	See Also
	--------
	`Text Area types <https://acbf.fandom.com/wiki/Body_Section_Definition#Text-area>`_.
	"""
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
	"""Allowed values for :attr:`Page.transition <libacbf.body.Page.transition>`.

	See Also
	--------
	`Page Transitions <https://acbf.fandom.com/wiki/Body_Section_Definition#Page>`_.
	"""
	fade = 0
	blend = auto()
	scroll_right = auto()
	scroll_down = auto()
	none = 100

class ImageRefType(Enum):
	"""Types of image references. Used by :attr:`ref_type <libacbf.body.Page.ref_type>`.

	See Also
	--------
	`Image Reference Types <https://acbf.fandom.com/wiki/Body_Section_Definition#Image>`_.
	"""
	Embedded = 0
	SelfArchived = auto()
	Archived = auto()
	Local = auto()
	URL = auto()

class ArchiveTypes(Enum):
	"""The type of the source archive file.
	Used by :attr:`ArchiveReader.type <libacbf.archivereader.ArchiveReader.type>`.
	"""
	Zip = 0
	SevenZip = auto()
	Tar = auto()
	Rar = auto()
