from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Tuple, Optional
import os
import distutils.util
import re
import magic
import requests
import langcodes
from pathlib import Path
from lxml import etree

if TYPE_CHECKING:
    from libacbf import ACBFBook
import libacbf.helpers as helpers
import libacbf.constants as consts
from libacbf.archivereader import ArchiveReader
from libacbf.bookdata import BookData


class Page:
    """A page in the book.

    See Also
    --------
    `Page Definition <https://acbf.fandom.com/wiki/Body_Section_Definition#Page>`_.

    Attributes
    ----------
    book : ACBFBook
        Book that this page belongs to.

    image_ref : str
        Reference to the image file. May be embedded in the ACBF file, in the ACBF archive, in an external archive,
        a local path or a URL. For information on how to format it,
        see `<https://acbf.fandom.com/wiki/Body_Section_Definition#Image>`_.

    ref_type : ImageRefType(Enum)
        A value from :class:`ImageRefType <libacbf.constants.ImageRefType>` indicating the type of reference in
        :attr:`Page.image_ref`.

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

    def __init__(self, page, book: ACBFBook, coverpage: bool = False):
        self._book = book
        self._nsmap = book._nsmap
        self._page = page

        self._arch_path = None
        self._file_path = None
        self._file_id = None

        self._image_ref = ''
        self._image = None

        self.text_layers: Dict[str, TextLayer] = {}
        self.frames = []
        self.jumps = []

        self.image_ref: str = ''

        self.is_coverpage: bool = coverpage
        self.ref_type: consts.ImageRefType = None

        # --- Optional ---
        if not coverpage:
            self.bgcolor: Optional[str] = None
            self.transition: Optional[consts.PageTransitions] = None
            self.title: Dict[str, str] = {}

            # BGColor
            if "bgcolor" in page.keys():
                self.bgcolor = page.attrib["bgcolor"]

            # Transition
            if "transition" in page.keys():
                self.transition = consts.PageTransitions[page.attrib["transition"]]

            # Title
            title_items = page.findall(f"{self._nsmap}title")
            for t in title_items:
                lang = '_'
                if "lang" in t.keys():
                    lang = langcodes.standardize_tag(t.attrib["lang"])
                self.title[lang] = t.text

        # Text Layers
        for lr in page.findall("text-layer", namespaces=self._nsmap):
            lang = langcodes.standardize_tag(lr.attrib["lang"])
            self.text_layers[lang] = TextLayer(lr, self._nsmap, self.book)

        # Frames
        for fr in page.findall("frame", namespaces=self._nsmap):
            frame = Frame(helpers.pts_to_vec(fr.attrib["points"]))
            if "bgcolor" in fr.keys():
                frame.bgcolor = fr.attrib["bgcolor"]
            self.frames.append(frame)

        # Jumps
        for jp in page.findall("jump", namespaces=self._nsmap):
            jump = Jump(helpers.pts_to_vec(jp.attrib["points"]), int(jp.attrib["page"]))
            self.jumps.append(jump)

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

        if ref.startswith("#"):
            self.ref_type = consts.ImageRefType.Embedded
            self._file_id = re.sub("#", '', ref)

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
    def set_transition(self, tr: str):
        """Set transition.

        Parameters
        ----------
        tr
        """
        if self.is_coverpage:
            raise AttributeError("`coverpage` has no attribute `transition`.")

        self.transition = consts.PageTransitions[tr]

    # Text Layers
    @helpers.check_book
    def add_textlayer(self, lang: str):
        lang = langcodes.standardize_tag(lang)
        tlangs = [langcodes.standardize_tag(x.attrib["lang"]) for x in self._page.findall(f"{self._ns}text-layer")]
        if lang in tlangs:
            return
        t_layer = etree.SubElement(self._page, f"{self._ns}text-layer", {"lang": lang})
        self.text_layers[lang] = TextLayer(t_layer, self._ns, self.book)

    @helpers.check_book
    def remove_textlayer(self, lang: str):
        if lang in self.text_layers:
            t_layer = self.text_layers.pop(lang)
            t_layer._layer.clear()
            self._page.remove(t_layer._layer)

    @helpers.check_book
    def change_textlayer_lang(self, src_lang: str, dest_lang: str):
        src_lang, dest_lang = map(langcodes.standardize_tag, (src_lang, dest_lang))
        t_layer = self.text_layers.pop(src_lang)
        t_layer._layer.set("lang", dest_lang)
        t_layer.lang = dest_lang
        self.text_layers[dest_lang] = t_layer

    # Frames
    @helpers.check_book
    def insert_new_frame(self, index: int, points: List[Tuple[int, int]]):
        fr_element = etree.Element(f"{self._ns}frame", {"points": helpers.vec_to_pts(points)})
        fr = Frame([helpers.Vec2(x, y) for x, y in points], self.book)
        fr._element = fr_element

        if len(self.frames) == 0:
            self.frames.append(fr)
            self._page.append(fr_element)
        elif index == len(self.frames):
            self.frames[-1]._element.addnext(fr_element)
            self.frames.append(fr)
        else:
            self.frames[index]._element.addprevious(fr_element)
            self.frames.insert(index, fr)

    @helpers.check_book
    def remove_frame(self, index: int):
        fr = self.frames.pop(index)
        fr._element.clear()
        self._page.remove(fr._element)

    @helpers.check_book
    def reorder_frame(self, src_index: int, dest_index: int):
        fr = self.frames.pop(src_index)
        if dest_index == len(self.frames):
            self._page.remove(fr._element)
            self.frames[-1]._element.addnext(fr._element)
        else:
            _ = self.frames[dest_index]  # Checks if index is in bounds before removing element
            self._page.remove(fr._element)
            self.frames[dest_index]._element.addprevious(fr._element)
        self.frames.insert(dest_index, fr)

    # Jumps
    @helpers.check_book
    def add_jump(self, target_page: int, points: List[Tuple[int, int]]):
        jp_element = etree.SubElement(self._page, f"{self._ns}jump")
        jp_element.set("page", str(target_page))
        jp_element.set("points", helpers.vec_to_pts(points))
        jp = Jump([helpers.Vec2(x, y) for x, y in points], target_page, self.book)
        jp._element = jp_element
        self._jumps.append(jp)

    @helpers.check_book
    def remove_jump(self, index: int):
        jp = self.jumps.pop(index)
        jp._element.clear()
        self._page.remove(jp._element)


class TextLayer:
    """Defines a text layer drawn on a page.

    See Also
    --------
    `Text Layer specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Text-layer>`_.

    Attributes
    ----------
    lang : str
        A standard language code that defines the language of the text in this layer.

    text_areas : List[TextArea]
        A list of :class:`TextArea` objects in order (order matters for text-to-speech).

    bgcolor : str, optional
        Defines the background colour of the text areas or inherits from :attr:`Page.bgcolor` if ``None``.
    """

    def __init__(self, layer, ns, book: ACBFBook):
        self.book = book
        self._layer = layer
        self._ns = ns

        self.bgcolor: Optional[str] = None
        if "bgcolor" in layer.keys():
            self.bgcolor = layer.attrib["bgcolor"]

        # Sub
        self.text_areas: List[TextArea] = []
        areas = layer.findall(f"{ns}text-area")
        for ar in areas:
            self.text_areas.append(TextArea(ar, ns, self.book))

    @helpers.check_book
    def set_bgcolor(self, bg: Optional[str]):
        if bg is not None:
            self._layer.set("bgcolor", bg)
        elif "bgcolor" in self._layer.attrib:
            self._layer.attrib.pop("bgcolor")
        self.bgcolor = bg

    @helpers.check_book
    def insert_new_textarea(self, idx: int, points: List[Tuple[int, int]], paragraph: str):
        ta = etree.Element(f"{self._ns}text-area")
        ta.set("points", helpers.vec_to_pts(points))
        ta.extend(helpers.para_to_tree(paragraph, self._ns))
        self._layer.insert(idx, ta)
        self.text_areas.insert(idx, TextArea(ta, self._ns, self.book))

    @helpers.check_book
    def remove_textarea(self, idx: int):
        ta = self.text_areas.pop(idx)
        ta._area.clear()
        self._layer.remove(ta._area)

    @helpers.check_book
    def reorder_textarea(self, src_index: int, dest_index: int):
        ta = self.text_areas.pop(src_index)
        self._layer.remove(ta._area)
        self._layer.insert(dest_index, ta._area)
        self.text_areas.insert(dest_index, ta)


class TextArea:
    """Defines an area where text is drawn.

    See Also
    --------
    `Text Area specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Text-area>`_.

    Attributes
    ----------
    points : List[2D Vectors]
        A list of named tuples with ``x`` and ``y`` values representing a 2-dimensional vector. ::

            sixth_point = <Item in TextArea list>.points[5]
            sixth_point.x # x-coordinate of point
            sixth_point.y # y-coordinate of point

    paragraph : str
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
        Defines the background colour of the text area or inherits from :attr:`TextLayer.bgcolor` if
        ``None``.

    rotation : int, optional
        Defines the rotation of the text layer.

        Can be an integer from 0 to 360.

    type : TextAreas(Enum), optional
        The type of text area. Rendering can be changed based on type.

        Allowed values are defined in :class:`TextAreas <libacbf.constants.TextAreas>`.

    inverted : bool, optional
        Whether text is rendered with inverted colour.

    transparent : bool, optional
        Whether text is drawn.
    """

    def __init__(self, area, ns, book: ACBFBook):
        self.book = book
        self._area = area
        self._ns = ns

        self.points: List[helpers.Vec2] = helpers.pts_to_vec(area.attrib["points"])

        self.paragraph: str = helpers.tree_to_para(area, ns)

        # Optional
        self.bgcolor: Optional[str] = None
        if "bgcolor" in area.keys():
            self.bgcolor = area.attrib["bgcolor"]

        self.rotation: Optional[int] = None
        if "text-rotation" in area.keys():
            rot = int(area.attrib["text-rotation"])
            if 0 <= rot <= 360:
                self.rotation = rot
            else:
                raise ValueError("Rotation must be an integer from 0 to 360.")

        self.type: Optional[consts.TextAreas] = None
        if "type" in area.keys():
            self.type = consts.TextAreas[area.attrib["type"]]

        self.inverted: Optional[bool] = None
        if "inverted" in area.keys():
            self.inverted = bool(distutils.util.strtobool(area.attrib["inverted"]))

        self.transparent: Optional[bool] = None
        if "transparent" in area.keys():
            self.transparent = bool(distutils.util.strtobool(area.attrib["transparent"]))

    # Editor
    @helpers.check_book
    def set_paragraph(self, paragraph: str):
        for i in self._area.iter():
            if i != self._area:
                i.clear()
                self._area.remove(i)
        self._area.extend(helpers.para_to_tree(paragraph, self._ns))
        self.paragraph = paragraph

    @helpers.check_book
    def insert_point(self, idx: int, x: int, y: int):
        self.points.insert(idx, helpers.Vec2(x, y))
        self._area.set("points", helpers.vec_to_pts(self.points))

    @helpers.check_book
    def append_point(self, x: int, y: int):
        self.points.append(helpers.Vec2(x, y))
        self._area.set("points", helpers.vec_to_pts(self.points))

    @helpers.check_book
    def set_point(self, idx: int, x: int, y: int):
        self.points[idx] = helpers.Vec2(x, y)
        self._area.set("points", helpers.vec_to_pts(self.points))

    @helpers.check_book
    def remove_point(self, idx: int):
        if len(self.points) == 1:
            raise ValueError("`points` cannot be empty.")
        self.points.pop(idx)
        self._area.set("points", helpers.vec_to_pts(self.points))

    # --- Optional ---
    @helpers.check_book
    def set_bgcolor(self, bg: Optional[str]):
        if bg is not None:
            self._area.set("bgcolor", bg)
        elif "bgcolor" in self._area.attrib:
            self._area.attrib.pop("bgcolor")
        self.bgcolor = bg

    @helpers.check_book
    def set_rotation(self, rot: Optional[int]):
        if rot is None:
            if "text-rotation" in self._area.keys():
                self._area.attrib.pop("text-rotation")
        elif 0 <= rot <= 360:
            self._area.set("text-rotation", str(rot))
        else:
            raise ValueError("Rotation must be an integer from 0 to 360.")
        self.rotation = rot

    @helpers.check_book
    def set_type(self, ty: Optional[str]):
        if ty is None:
            if "type" in self._area.keys():
                self._area.attrib.pop("type")
            self.type = None
        else:
            ty = consts.TextAreas[ty]
            self._area.set("type", ty.name)
            self.type = ty

    @helpers.check_book
    def set_inverted(self, inv: Optional[bool]):
        if inv is None:
            if "inverted" in self._area.keys():
                self._area.attrib.pop("inverted")
        else:
            self._area.set("inverted", str(inv).lower())
        self.inverted = inv

    @helpers.check_book
    def set_transparent(self, tra: Optional[bool]):
        if tra is None:
            if "transparent" in self._area.keys():
                self._area.attrib.pop("transparent")
        else:
            self._area.set("transparent", str(tra).lower())
        self.transparent = tra


class Frame:
    """A subsection of a page.

    See Also
    --------
    `Frame specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Frame>`_.

    Attributes
    ----------
    points : List[2D Vectors]
        A list of named tuples with ``x`` and ``y`` values representing a 2-dimensional vector. Same as
        :attr:`TextArea.points`.

    bgcolor : str, optional
        Defines the background colour for the page. Inherits from :attr:`Page.bgcolor <libacbf.body.Page.bgcolor>`if
        ``None``.
    """

    def __init__(self, points: List[helpers.Vec2], book: ACBFBook):
        self.book = book
        self._element = None

        self.points: List[helpers.Vec2] = points
        self.bgcolor: Optional[str] = None

    @helpers.check_book
    def insert_point(self, idx: int, x: int, y: int):
        self.points.insert(idx, helpers.Vec2(x, y))
        self._element.set("points", helpers.vec_to_pts(self.points))

    @helpers.check_book
    def set_point(self, idx: int, x: int, y: int):
        self.points[idx] = helpers.Vec2(x, y)
        self._element.set("points", helpers.vec_to_pts(self.points))

    @helpers.check_book
    def remove_point(self, idx: int):
        if len(self.points) == 1:
            raise ValueError("`points` cannot be empty.")
        self.points.pop(idx)
        self._element.set("points", helpers.vec_to_pts(self.points))

    @helpers.check_book
    def set_bgcolor(self, bg: Optional[str]):
        if bg is not None:
            self._element.set("bgcolor", bg)
        elif "bgcolor" in self._element.attrib:
            self._element.attrib.pop("bgcolor")
        self.bgcolor = bg


class Jump:
    """Clickable area on a page which navigates to another page.

    See Also
    --------
    `body Info Jump specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Jump>`_.

    Attributes
    ----------
    points : List[2D Vectors]
        A list of named tuples with ``x`` and ``y`` values representing a 2-dimensional vector. Same as
        :attr:`TextArea.points`.

    page : int
        Target page to go to when clicked. Cover page is ``0``, first page is ``1``, second page is ``2`` and so on.
    """

    def __init__(self, points: List[helpers.Vec2], page: int, book: ACBFBook):
        self.book = book
        self._element = None

        self.page: int = page
        self.points: List[helpers.Vec2] = points

    @helpers.check_book
    def set_target_page(self, target_page: int):
        self._element.set("page", str(target_page))
        self.page = target_page

    @helpers.check_book
    def insert_point(self, idx: int, x: int, y: int):
        self.points.insert(idx, helpers.Vec2(x, y))
        self._element.set("points", helpers.vec_to_pts(self.points))

    @helpers.check_book
    def set_point(self, idx: int, x: int, y: int):
        self.points[idx] = helpers.Vec2(x, y)
        self._element.set("points", helpers.vec_to_pts(self.points))

    @helpers.check_book
    def remove_point(self, idx: int):
        if len(self.points) == 1:
            raise ValueError("`points` cannot be empty.")
        self.points.pop(idx)
        self._element.set("points", helpers.vec_to_pts(self.points))
