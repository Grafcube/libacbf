"""
Warnings
--------

The values of the enum members don't matter and there is no guarantee that they will never change. If you have to use
it, use strings instead (case sensitive). ::

    activity = AuthorActivities.Artist.name

    # Check if value exists
    _ = AuthorActivities["Writer"]  # No `KeyError` exception
    _ = AuthorActivities["asdfgh"]  # `KeyError` exception is raised
"""
from enum import Enum, auto


class AuthorActivities(Enum):
    """List of accepted values for :attr:`Author.activity <libacbf.metadata.Author.activity>`.
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
    Other = auto()


class Genres(Enum):
    """List of accepted values for keys of :attr:`book_info.genres <libacbf.libacbf.BookInfo.genres>`.
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
    other = auto()


class TextAreas(Enum):
    """Types of text areas. Used by :attr:`TextArea.type <libacbf.body.TextArea.type>`.
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
    """
    fade = 0
    blend = auto()
    scroll_right = auto()
    scroll_down = auto()
    none = auto()


class ImageRefType(Enum):
    """Types of image references. Used by :attr:`Page.ref_type <libacbf.body.Page.ref_type>`.
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
