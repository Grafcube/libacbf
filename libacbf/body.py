from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Tuple, Optional
import os
import re
import magic
import requests
from pathlib import Path

if TYPE_CHECKING:
    from libacbf import ACBFBook
import libacbf.helpers as helpers
import libacbf.constants as consts
from libacbf.archivereader import ArchiveReader
from libacbf.bookdata import BookData


class Page:
    r"""A page in the book.

    See Also
    --------
    `Page Definition <https://acbf.fandom.com/wiki/Body_Section_Definition#Page>`_.

    Attributes
    ----------
    image_ref : str
        Reference to the image file. May be embedded in the ACBF file, in the ACBF archive, in an external archive,
        a local path or a URL.

        There are several ways to format it to read data:

        Reference to a file embedded in :class:`ACBFBook.data <libacbf.libacbf.ACBFData>`:
            - ``“#page1.jpg“``

        Reference to a file on disk:
            - ``“/path/to/file/page1.jpg“``
            - ``"C:\path\to\file\page1.jpg"``
            - ``“file:///path/to/file/page1.jpg“``
            - ``“file://C:\path\to\file\page1.jpg“``

        Path to a file in the book's archive or relative path to file on disk if book is a plain ACBF XML:
            - ``“page1.jpg“``
            - ``“images/page1.jpg“``

        Reference to file in an archive:
            - ``“zip:path/to/archive.zip!/path/to/file/page1.jpg“``

        URL address containing the image:
            - ``“https://example.com/book1/images/page1.jpg“``

    ref_type : ImageRefType(Enum)
        A value from :class:`ImageRefType <libacbf.constants.ImageRefType>` indicating the type of reference in
        :attr:`Page.image_ref`.

    text_layers: Dict[str, TextLayer]
        A dictionary with keys being the language of the text layer and values being :class:`TextLayer` objects.

    frames: List[Frame]
        A list of :class:`Frame` objects in order of appearance.

    jumps: List[Jump]
        A list of :class:`Jump` objects.

    Warnings
    --------
    The attributes ``title``, ``bgcolor`` and ``transition`` are not available on
    :attr:`ACBFBook.book_info.coverpage <libacbf.libacbf.BookInfo.coverpage>`.

    Attributes
    ----------
    title : Dict[str, str], optional
        It is used to define beginning of chapters, sections of the book and can be used to create a table of contents.
        Keys are standard language codes or ``'_'`` if not defined. Values are titles as string.

    bgcolor : str, optional
        Defines the background colour for the page. Inherits from
        :attr:`ACBFBody.bgcolor <libacbf.libacbf.ACBFBody.bgcolor>` if ``None``.

    transition: PageTransitions(Enum), optional
        Defines the type of transition from the previous page to this one. Allowed values are in
        :class:`PageTransitions <libacbf.constants.PageTransitions>`.
    """

    def __init__(self, image_ref: str, book: ACBFBook, coverpage: bool = False):
        self._book = book  # Required to get embedded and archived images in `image` property

        self._arch_path = None
        self._file_path = None
        self._file_id = None

        self._image = None

        self.is_coverpage: bool = coverpage
        self.ref_type: consts.ImageRefType = None
        self.image_ref = image_ref  # Set property

        self.text_layers: Dict[str, TextLayer] = {}
        self.frames: List[Frame] = []
        self.jumps: List[Jump] = []

        # --- Optional ---
        if not coverpage:
            self.bgcolor: Optional[str] = None
            self.transition: Optional[consts.PageTransitions] = None
            self.title: Dict[str, str] = {}

    def __repr__(self):
        if self.is_coverpage:
            return f'<libacbf.BookInfo.coverpage as `Page` href="{self.image_ref}">'
        else:
            return f'<libacbf.body.Page href="{self.image_ref}">'

    @property
    def image_ref(self) -> str:
        return self._image_ref

    @image_ref.setter
    def image_ref(self, ref: str):
        self._image = None

        if ref.startswith('#'):
            self.ref_type = consts.ImageRefType.Embedded
            self._file_id = re.sub('#', '', ref)

        elif ref.startswith("zip:"):
            self.ref_type = consts.ImageRefType.Archived
            ref_path = re.sub("zip:", '', ref)
            self._arch_path = Path(re.split("!", ref_path)[0])
            self._file_path = Path(re.split("!", ref_path)[1])
            self._file_id = self._file_path.name
            if not os.path.isabs(self._arch_path):
                self._arch_path = Path(os.path.abspath(str(self._arch_path)))

        elif re.fullmatch(helpers.url_pattern, ref):
            self.ref_type = consts.ImageRefType.URL
            self._file_id = re.split("/", ref)[-1]

        else:
            if ref.startswith("file://"):
                self._file_path = Path(os.path.abspath(ref))
            else:
                self._file_path = Path(ref)

            if os.path.isabs(ref):
                self.ref_type = consts.ImageRefType.Local
            else:
                if self._book.archive is not None:
                    self.ref_type = consts.ImageRefType.SelfArchived
                else:
                    self.ref_type = consts.ImageRefType.Local
                    self._file_path = self._book.book_path.parent / self._file_path

            self._file_id = self._file_path.name

        self._image_ref: str = ref

    @property
    def image(self) -> BookData:
        """Gets the image data from the source.

        Returns
        -------
        BookData
            A :class:`BookData <libacbf.bookdata.BookData>` object.
        """
        if self._image is None:
            if self.ref_type == consts.ImageRefType.Embedded:
                self._image = self._book.data[self._file_id]
                return self._image

            elif self.ref_type == consts.ImageRefType.Archived:
                with ArchiveReader(self._arch_path) as ext_archive:
                    contents = ext_archive.read(str(self._file_path))

            elif self.ref_type == consts.ImageRefType.URL:
                response = requests.get(self.image_ref)
                contents = response.content

            else:
                if self.ref_type == consts.ImageRefType.SelfArchived:
                    contents = self._book.archive.read(str(self._file_path))
                elif self.ref_type == consts.ImageRefType.Local:
                    with open(str(self._file_path), "rb") as image:
                        contents = image.read()

            contents_type = magic.from_buffer(contents, True)
            self._image = BookData(self._file_id, contents_type, contents)

        return self._image

    @helpers.check_book
    def set_transition(self, tr: Optional[str]):
        """Set transition by string.

        Parameters
        ----------
        tr : str | None
            Transition value to be set. Pass ``None`` to remove.
        """
        if self.is_coverpage:
            raise AttributeError("`coverpage` has no attribute `transition`.")

        self.transition = consts.PageTransitions[tr] if tr is not None else tr

    @helpers.check_book
    def add_textlayer(self, lang: str, *areas: TextArea) -> TextLayer:
        """Add a text layer to the page.

        Parameters
        ----------
        lang : str
            The language of the text layer.

        *areas : TextArea, optional
            TextArea objects to fill the layer with.

        Returns
        -------
        TextLayer
            The newly created text layer.
        """
        tl = TextLayer(*areas)
        self.text_layers[lang] = tl
        return tl

    @helpers.check_book
    def insert_frame(self, index: int, points: List[Tuple[int, int]]) -> Frame:
        """Insert a frame at the index.

        Parameters
        ----------
        index : int
            Index to insert at.

        points : List[Tuple[int, int]]
            The points defining the frame.

        Returns
        -------
        Frame
            The newly created frame.
        """
        fr = Frame(points)
        self.frames.insert(index, fr)
        return fr

    @helpers.check_book
    def append_frame(self, points: List[Tuple[int, int]]) -> Frame:
        """Append a frame to the page.

        Returns
        -------
        Frame
            The newly created frame.
        """
        fr = Frame(points)
        self.frames.append(fr)
        return fr

    @helpers.check_book
    def add_jump(self, target: int, points: List[Tuple[int, int]]) -> Jump:
        """Add a jump to the page.

        Parameters
        ----------
        target : int
            The target page. ``0`` is the cover page, ``1`` is the first page, ``2`` is the second page etc.

        points : List[Tuple[int, int]]
            The points defining the jump.

        Returns
        -------
        Jump
            The newly created jump.
        """
        jp = Jump(target, points, self._book)
        self.jumps.append(jp)
        return jp


class TextLayer:
    """Defines a text layer drawn on a page.

    See Also
    --------
    `Text Layer specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Text-layer>`_.

    Attributes
    ----------
    text_areas : List[TextArea]
        A list of :class:`TextArea` objects in order (order matters for text-to-speech).

    bgcolor : str, optional
        Defines the background colour of the text areas or inherits from :attr:`Page.bgcolor` if ``None``.
    """

    def __init__(self, *areas: TextArea):
        self.text_areas: List[TextArea] = list(areas)
        self.bgcolor: Optional[str] = None

    def insert_textarea(self, index: int, text: str, points: List[Tuple[int, int]]) -> TextArea:
        """Insert a text area at the index.

        Parameters
        ----------
        index : int
            Index to insert at.

        text : str
            Multiline text of the text area.

        points : List[Tuple[int, int]]
            The points that define the text area.

        Returns
        -------
            The newly created text area.
        """
        ta = TextArea(text, points)
        self.text_areas.insert(index, ta)
        return ta

    def append_textarea(self, text: str, points: List[Tuple[int, int]]) -> TextArea:
        """Append a text area to the layer.

        Parameters
        ----------
        text : str
            Multiline text of the text area.

        points : List[Tuple[int, int]]
            The points that define the text area.

        Returns
        -------
            The newly created text area.
        """
        ta = TextArea(text, points)
        self.text_areas.append(ta)
        return ta


class TextArea:
    """Defines an area where text is drawn.

    See Also
    --------
    `Text Area specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Text-area>`_.

    Attributes
    ----------
    points : List[Tuple[int, int]]
        A list of tuples as coordinates.

    text : str
        A multiline string of what text to show in the are. Can have special tags for formatting.

        <strong>...</strong>
            Bold letters.

        <emphasis>...</emphasis>
            Italicised or cursive text.

        <strikethrough>...</strikethrough>
            Striked-through text.

        <sub>...</sub>
            Subscript text.

        <sup>...</sup>
            Superscript text.

        <a href=“...“>...</a>
            A link. Internal or external.

    bgcolor : str, optional
        Defines the background colour of the text area or inherits from :attr:`TextLayer.bgcolor` if ``None``.

    rotation : int, optional
        Defines the rotation of the text layer.

        Can be an integer from 0 to 360.

    type : TextAreas(Enum), optional
        The type of text area. Rendering can be changed based on type. Allowed values are defined in
        :class:`TextAreas <libacbf.constants.TextAreas>`.

    inverted : bool, optional
        Whether text is rendered with inverted colour.

    transparent : bool, optional
        Whether text is drawn.
    """

    def __init__(self, text: str, points: List[Tuple[int, int]]):
        self.text: str = text
        self.points: List[Tuple[int, int]] = points

        # --- Optional ---
        self.bgcolor: Optional[str] = None
        self.rotation: Optional[int] = None
        self.type: Optional[consts.TextAreas] = None
        self.inverted: Optional[bool] = None
        self.transparent: Optional[bool] = None

    def set_type(self, ty: Optional[str]):
        """Set type by string.

        Parameters
        ----------
        ty : str | None
            Type to set or ``None`` to remove.
        """
        self.type = consts.TextAreas[ty] if ty is not None else ty


class Frame:
    """A subsection of a page.

    See Also
    --------
    `Frame specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Frame>`_.

    Attributes
    ----------
    points : List[Tuple[int, int]]
        A list of tuples as coordinates.

    bgcolor : str, optional
        Defines the background colour for the page. Inherits from :attr:`Page.bgcolor <libacbf.body.Page.bgcolor>` if
        ``None``.
    """

    def __init__(self, points: List[Tuple[int, int]]):
        self.points: List[Tuple[int, int]] = points
        self.bgcolor: Optional[str] = None


class Jump:
    """Clickable area on a page which navigates to another page.

    See Also
    --------
    `body Info Jump specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Jump>`_.

    Attributes
    ----------
    target : int
        The target page index. Cover page is ``0``, first page is ``1``, second page is ``2`` and so on.

    points : List[Tuple[int, int]]
        A list of tuples as coordinates.
    """

    def __init__(self, target: int, points: List[Tuple[int, int]], book: ACBFBook):
        self._book = book

        self.target = target
        self.points: List[Tuple[int, int]] = points

    @property
    def page(self) -> Page:
        """Target page to go to when clicked.
        """
        if self.target == 0:
            return self._book.book_info.coverpage
        else:
            return self._book.body.pages[self.target]
