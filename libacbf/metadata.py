from __future__ import annotations

import langcodes
from typing import Optional, Union

import libacbf.constants as constants


class Author:
    """Defines an author of the comic book. An author must at least have a nickname not be ``None`` or have both
    first name and last name not be ``None``.

    See Also
    --------
    `Author specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Author>`_.

    Examples
    --------
    An ``Author`` object can be created with either a nickname, a first and last name or both. ::

        from libacbf import ACBFBook

        with ACBFBook("path/to/book.cbz", 'w') as book:
            au = Author("Hugh", "Mann")
            # au.first_name == "Hugh"
            # au.last_name == "Mann"

            au = Author("NotAPlatypus")
            # au.nickname == "NotAPlatypus"

            au = Author("Hugh", "Mann", "NotAPlatypus")
            # au.first_name == "Hugh"
            # au.last_name == "Mann"
            # au.nickname == "NotAPlatypus"

    This is also possible. ::

        au = Author(first_name="Hugh", last_name="Mann", nickname="NotAPlatypus")

    Attributes
    ----------
    first_name : str
        Author's first name.

    last_name : str
        Author's last name.

    nickname : str
        Author's nickname.

    middle_name : str, optional
        Author's middle name.

    home_page : str, optional
        Author's website.

    email : str, optional
        Author's email address.
    """

    def __init__(self, *names: str, first_name=None, last_name=None, nickname=None):
        self._first_name: Optional[str] = None
        self._last_name: Optional[str] = None
        self._nickname: Optional[str] = None

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
            self._first_name: Optional[str] = first_name
            self._last_name: Optional[str] = last_name
            self._nickname: Optional[str] = nickname
        else:
            raise ValueError("Author must have either First Name and Last Name or Nickname.")

        self._activity: Optional[constants.AuthorActivities] = None
        self._lang: Optional[str] = None
        self.middle_name: Optional[str] = None
        self.home_page: Optional[str] = None
        self.email: Optional[str] = None

    def __repr__(self):
        return f'<libacbf.metadata.Author first_name="{self.first_name}" ' \
               f'last_name="{self.last_name}" nickname="{self.nickname}">'

    @property
    def first_name(self) -> Optional[str]:
        return self._first_name

    @first_name.setter
    def first_name(self, val: Optional[str]):
        if val is not None:
            self._first_name = val
        elif self.nickname is not None:
            self._first_name = val
        else:
            raise ValueError("Author must have either First Name and Last Name or Nickname.")

    @property
    def last_name(self) -> Optional[str]:
        return self._last_name

    @last_name.setter
    def last_name(self, val: Optional[str]):
        if val is not None:
            self._last_name = val
        elif self.nickname is not None:
            self._last_name = val
        else:
            raise ValueError("Author must have either First Name and Last Name or Nickname.")

    @property
    def nickname(self) -> Optional[str]:
        return self._nickname

    @nickname.setter
    def nickname(self, val: Optional[str]):
        if val is None and self.first_name is None:
            raise ValueError("Author must have either First Name and Last Name or Nickname.")
        self._nickname = val

    @property
    def activity(self) -> Optional[constants.AuthorActivities]:
        """Defines the activity that a particular author carried out on the comic book. Allowed values are defined in
        :class:`AuthorActivities <libacbf.constants.AuthorActivities>`.

        Returns
        -------
        AuthorActivities(Enum) | None
            A value from :class:`AuthorActivities <libacbf.constants.AuthorActivities>` enum or ``None`` if not defined.
        """
        return self._activity

    @activity.setter
    def activity(self, val: Optional[Union[str, constants.AuthorActivities]]):
        if isinstance(val, str):
            val = constants.AuthorActivities[val]
        self._activity = val

    @property
    def lang(self) -> Optional[str]:
        """Defines the language that the author worked in.

        Returns
        -------
        str | None
            Returns a standard language code or ``None`` if not defined.
        """
        return self._lang

    @lang.setter
    def lang(self, val: Optional[str]):
        if val is not None:
            val = langcodes.standardize_tag(val)
        self._lang = val

    def copy(self):
        """Returns a copy of this object.
        """
        copy = Author(self.first_name, self.last_name, self.nickname)
        copy.activity = self.activity
        copy.lang = self.lang
        copy.middle_name = self.middle_name
        copy.home_page = self.home_page
        copy.email = self.email
        return copy


class LanguageLayer:
    """Used by :attr:`ACBFBook.book_info.languages <libacbf.libacbf.BookInfo.languages>`.

    See Also
    --------
    `Book Info Languages specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Languages>`_.

    Attributes
    ----------
    lang : str
        Language of the layer as a standard language code.

    show : bool
        Whether the layer is drawn.
    """

    def __init__(self, lang: str, show: bool):
        self.lang: str = lang
        self.show: bool = show

    def __repr__(self):
        return f'<libacbf.metadata.LanguageLayer lang="{self.lang}" show="{self.show}">'

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, val: str):
        self._lang = langcodes.standardize_tag(val)


class Series:
    """Used by :attr:`ACBFBook.book_info.series <libacbf.libacbf.BookInfo.series>`.

    See Also
    --------
    `Book Info Sequence specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Sequence>`_.

    Attributes
    ----------
    sequence : str
        The book's position/entry in the series.

    volume : str, optional
        The volume that the book belongs to.
    """

    def __init__(self, sequence: str, volume: Optional[str] = None):
        self.sequence: str = sequence
        self.volume: Optional[str] = volume

    def __repr__(self):
        return f'<libacbf.metadata.Series sequence="{self.sequence}" volume="{self.volume}">'


class DBRef:
    """Used by :attr:`ACBFBook.book_info.database_ref <libacbf.libacbf.BookInfo.database_ref>`.

    See Also
    --------
    `Book Info DatabaseRef specifications <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#DatabaseRef>`_.

    Attributes
    ----------
    dbname : str
        Name of the database.

    reference : str
        Reference of the book in the database.

    type : str, optional
        Type of the given reference such as URL, ID etc.
    """

    def __init__(self, dbname: str, ref: str, type: Optional[str] = None):
        self.dbname: str = dbname
        self.reference: str = ref
        self.type: Optional[str] = type

    def __repr__(self):
        return f'<libacbf.metadata.DBRef dbname="{self.dbname}" reference="{self.reference}" type="{self.type}">'
