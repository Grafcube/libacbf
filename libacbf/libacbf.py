import re
import warnings
import magic
import distutils.util
import dateutil.parser
import langcodes
from io import UnsupportedOperation
from pathlib import Path
from datetime import date
from typing import List, Dict, Optional, Set, Union, Literal, IO
from base64 import b64encode
from lxml import etree
from zipfile import ZipFile
from py7zr import SevenZipFile
import tarfile as tar

import libacbf.helpers as helpers
import libacbf.constants as consts
import libacbf.metadata as metadata
import libacbf.body
from libacbf.bookdata import BookData
from libacbf.archivereader import ArchiveReader, get_archive_type
from libacbf.exceptions import InvalidBook, EditRARArchiveError, UnsupportedArchive


def _validate_acbf(tree, ns: str):
    """Validate XML tree with XSD.
    """
    version = re.split(r'/', ns)[-1]
    xsd_path = f"libacbf/schema/acbf-{version}.xsd"

    with open(xsd_path, encoding="utf-8") as file:
        acbf_root = etree.fromstring(bytes(file.read(), encoding="utf-8"))

    acbf_tree = acbf_root.getroottree()
    acbf_schema = etree.XMLSchema(acbf_tree)

    if version == "1.0":
        try:
            acbf_schema.assertValid(tree)
        except etree.DocumentInvalid as err:
            warnings.warn("Validation failed. Books with 1.0 schema are not fully supported.\n"
                          "Change the ACBF tag at the top of the `.acbf` XML file to "
                          '`<ACBF xmlns="http://www.acbf.info/xml/acbf/1.1">` to use the 1.1 schema.', UserWarning)
            warnings.warn(str(err), UserWarning)
    else:
        acbf_schema.assertValid(tree)


def _update_authors(author_items, nsmap) -> List[metadata.Author]:
    """Takes a list of etree elements and returns a list of Author objects.
    """
    authors = []

    for au in author_items:
        first_name = None
        last_name = None
        nickname = None
        if au.find("first-name", namespaces=nsmap) is not None:
            first_name = au.find("first-name", namespaces=nsmap).text
        if au.find("last-name", namespaces=nsmap) is not None:
            last_name = au.find("last-name", namespaces=nsmap).text
        if au.find("nickname", namespaces=nsmap) is not None:
            nickname = au.find("nickname", namespaces=nsmap).text

        author: metadata.Author = metadata.Author(first_name, last_name, nickname)

        if "activity" in au.keys():
            author.activity = au.attrib["activity"]
        if "lang" in au.keys():
            author.lang = au.attrib["lang"]

        # Optional
        if au.find("middle-name", namespaces=nsmap) is not None:
            author.middle_name = au.find("middle-name", namespaces=nsmap).text
        if au.find("home-page", namespaces=nsmap) is not None:
            author.home_page = au.find("home-page", namespaces=nsmap).text
        if au.find("email", namespaces=nsmap) is not None:
            author.email = au.find("email", namespaces=nsmap).text

        authors.append(author)

    return authors


def _edit_date(section, attr_s: str, attr_d: str, dt: Union[str, date], include_date: bool = True):
    """Common function to edit a date property.
    """
    if isinstance(dt, str):
        date_text = dt
    else:
        date_text = dt.isoformat()
    setattr(section, attr_s, date_text)

    date_val = None
    if include_date:
        date_val = dt
        if isinstance(dt, str):
            date_val = dateutil.parser.parse(dt, fuzzy=True).date()
    setattr(section, attr_d, date_val)


def _fill_page(pg, page, nsmap, book):
    """Fill Page data from XML tree.
    """
    for fr in pg.findall("frame", namespaces=nsmap):
        frame = libacbf.body.Frame(helpers.pts_to_vec(fr.attrib["points"]))
        if "bgcolor" in fr.keys():
            frame.bgcolor = fr.attrib["bgcolor"]
        page.frames.append(frame)

    for jp in pg.findall("jump", namespaces=nsmap):
        jump = libacbf.body.Jump(helpers.pts_to_vec(jp.attrib["points"]), int(jp.attrib["page"]), book)
        page.jumps.append(jump)

    # Text Layers
    for tl in pg.findall("text-layer", namespaces=nsmap):
        lang = langcodes.standardize_tag(tl.attrib["lang"])
        layer = libacbf.body.TextLayer()
        page.text_layers[lang] = layer

        if "bgcolor" in tl.keys():
            layer.bgcolor = tl.attrib["bgcolor"]

        # Text Areas
        for ta in tl.findall("text-area", namespaces=nsmap):
            text = helpers.tree_to_para(ta, nsmap)
            pts = helpers.pts_to_vec(ta.attrib["points"])
            area = libacbf.body.TextArea(text, pts)
            layer.text_areas.append(area)

            if "bgcolor" in ta.keys():
                area.bgcolor = ta.attrib["bgcolor"]

            if "text-rotation" in ta.keys():
                rot = int(ta.attrib["text-rotation"])
                if 0 <= rot <= 360:
                    area.rotation = rot
                else:
                    raise ValueError("Rotation must be an integer from 0 to 360.")

            if "type" in ta.keys():
                area.type = consts.TextAreas[ta.attrib["type"]]

            if "inverted" in ta.keys():
                area.inverted = bool(distutils.util.strtobool(ta.attrib["inverted"]))

            if "transparent" in ta.keys():
                area.transparent = bool(distutils.util.strtobool(ta.attrib["transparent"]))


def _get_root_template(nsmap: Dict):
    """Get the lxml root tree for a basic ACBF book.

    Parameters
    ----------
    nsmap : dict
        Namespaces
    """
    ns = f"{{{nsmap[None]}}}"

    root = etree.Element(f"{ns}ACBF", nsmap=nsmap)
    meta = etree.SubElement(root, f"{ns}meta-data", nsmap=nsmap)
    etree.SubElement(root, f"{ns}body", nsmap=nsmap)

    etree.SubElement(meta, f"{ns}book-info", nsmap=nsmap)

    publish_info = etree.SubElement(meta, f"{ns}publish-info", nsmap=nsmap)
    etree.SubElement(publish_info, f"{ns}publisher", nsmap=nsmap)
    etree.SubElement(publish_info, f"{ns}publish-date", nsmap=nsmap)

    document_info = etree.SubElement(meta, f"{ns}document-info", nsmap=nsmap)
    etree.SubElement(document_info, f"{ns}creation-date", nsmap=nsmap)

    return root


def get_book_template(ns: str = None) -> str:
    """Get the bare minimum XML required to create an ACBF book.

    Warnings
    --------
    Some properties will already exist and have default values. See (INSERT LINK HERE) for more details.

    Returns
    -------
    str
        XML string template.
    """
    if ns is None:
        ns = helpers.namespaces["1.1"]

    return etree.tostring(_get_root_template({None: ns}).getroottree(),
                          encoding="utf-8",
                          xml_declaration=True,
                          pretty_print=True
                          ).decode("utf-8")


class ACBFBook:
    """Base class for reading ACBF ebooks.

    Parameters
    ----------
    file : str | Path | IO
        Path or file object to write ACBF book to. May be absolute or relative.

    mode : 'r' | 'w' | 'a' | 'x', default='r'
        The mode to open the file in. Defaults to read-only mode.

        r
            Read only mode. No editing is possible. Can read ACBF, Zip, 7Zip, Tar and Rar formatted books.
        w
            Overwrite file with new file. Raises exception for Rar archive types.
        a
            Edit the book without truncating. Raises exception for Rar archive types.
        x
            Exclusive write to file. Raises ``FileExists`` exception if file already exists. Only works for file
            paths. Raises exception for Rar archive types.

    archive_type : str | None, default="Zip"
        The type of ACBF book that the file is. If ``None`` Then creates a plain XML book. Otherwise creates archive of
        format. Accepted string values are listed at :class:`ArchiveTypes <libacbf.constants.ArchiveTypes>`.

        Warning
        -------
        You do not have to specify the type of archive unless you are creating a new one. The correct type will be
        determined regardless of this parameter's value. Use this when you want to create a new book.

    Raises
    ------
    EditRARArchiveError
        Raised if ``mode`` parameter is not ``'r'`` but file is a Rar archive.

    InvalidBook
        Raised if the XML does not match ACBF schema or if archive does not contain ACBF file.

    See Also
    --------
    `ACBF Specifications <https://acbf.fandom.com/wiki/Advanced_Comic_Book_Format_Wiki>`_.

    Notes
    -----
    Archive formats use the defaults of each type like compression level etc. Manage the archives yourself if you want
    to change this. Image refs that are relative paths check within the archive if the book is an archive. Otherwise it
    checks relative to the '.acbf' file. So you can simply use a directory to manage the book and archive it with your
    own settings when you are done.

    Examples
    --------
    A book object can be opened, read and then closed. ::

        from libacbf import ACBFBook

        book = ACBFBook("path/to/file.cbz")
        # Read data from book
        book.close()

    ``ACBFBook`` is also a context manager and can be used in with statements. ::

        from libacbf import ACBFBook

        with ACBFBook("path/to/file.cbz") as book:
            # Read data from book

    You can pass a ``BytesIO`` object. Keep in mind that you cannot use ``mode='x'`` in this case. ::

        import io
        from libacbf import ACBFBook

        file = io.BytesIO()

        with ACBFBook(file, 'w') as book:
            # Write data to book

    Attributes
    ----------
    book_info : BookInfo
        See :class:`BookInfo` for more information.

    publisher_info : PublishInfo
        See :class:`PublishInfo` for more information.

    document_info : DocumentInfo
        See :class:`DocumentInfo` for more information.

    body : ACBFBody
        See :class:`ACBFBody` for more information.

    data : ACBFData
        See :class:`ACBFData` for more information.

    references : dict
        A dictionary that contains a list of particular references that occur inside the
        main document body. Keys are unique reference ids and values are dictionaries that contain
        a ``'_'`` key with text. ::

            {
                "ref_id_001": {
                    "_": "This is a reference."
                }
                "ref_id_002": {
                    "_": "This is another reference."
                }
            }

        ``'_'`` can contain special tags for formatting. For more information and a full list,
        see :attr:`TextArea.text <libacbf.body.TextArea.text>`.

    styles : Styles
        See :class:`Styles` for more information.

    archive : ArchiveReader | None
        Can be used to read archive directly if file is not plain ACBF. Use this if you want to read exactly what
        files the book contains but try to avoid directly writing files through ``ArchiveReader``.
    """

    def __init__(self, file: Union[str, Path, IO], mode: Literal['r', 'w', 'a', 'x'] = 'r',
                 archive_type: Optional[str] = "Zip"):
        self._source = file
        self.book_path: Path = None
        self.archive: Optional[ArchiveReader] = None
        self.mode: Literal['r', 'w', 'a', 'x'] = mode
        self.is_open: bool = True

        if isinstance(file, str):
            self.book_path = Path(file).resolve()
        if isinstance(file, Path):
            self.book_path = file.resolve()

        archive_type = consts.ArchiveTypes[archive_type] if archive_type is not None else archive_type
        is_text = archive_type is None

        if mode in ('r', 'a'):
            try:
                archive_type = get_archive_type(file)
                is_text = False
            except UnsupportedArchive:
                archive_type = None
                is_text = True

        if archive_type == consts.ArchiveTypes.Rar and mode != 'r':
            raise EditRARArchiveError

        def create_file():
            if not is_text:
                if archive_type == consts.ArchiveTypes.Zip:
                    with ZipFile(file, 'w') as _:
                        pass
                elif archive_type == consts.ArchiveTypes.SevenZip:
                    with SevenZipFile(file, 'w') as _:
                        pass
                elif archive_type == consts.ArchiveTypes.Tar:
                    with tar.open(file, 'w') as _:
                        pass

                self.archive = ArchiveReader(file, 'w')
                name = self.book_path.stem + ".acbf" if self.book_path is not None else "book.acbf"
                self.archive.write(get_book_template().encode("utf-8"), name)
            else:
                if self.book_path is not None:
                    with open(str(self.book_path), 'w') as book:
                        book.write(get_book_template())
                else:
                    file.write(get_book_template().encode("utf-8"))

        if mode in ('r', 'a'):
            if self.book_path is not None and not self.book_path.is_file():
                raise FileNotFoundError

            if mode == 'a' and not is_text:
                self.archive = ArchiveReader(file, 'w')
                if self.archive._get_acbf_file() is None:
                    name = Path(self.archive.filename).stem + ".acbf" \
                        if self.archive.filename is not None \
                        else "book.acbf"

                    self.archive.write(get_book_template().encode("utf-8"), name)

        elif mode == 'x':
            if self.book_path is not None:
                if self.book_path.is_file():
                    raise FileExistsError
                else:
                    create_file()
            else:
                raise FileExistsError

        elif mode == 'w':
            create_file()

        arc_mode = 'w' if mode in ('w', 'a', 'x') else 'r'

        if not is_text:
            if self.archive is None:
                self.archive = ArchiveReader(file, arc_mode)
            acbf_file = self.archive._get_acbf_file()
            if acbf_file is None:
                raise InvalidBook
            contents = self.archive.read(acbf_file)
        else:
            if self.book_path is None:
                contents = file.read()
            else:
                with open(file, 'r') as book:
                    contents = book.read()

        if isinstance(contents, bytes):
            contents = contents.decode("utf-8")

        self._root = etree.fromstring(bytes(contents, "utf-8"))
        self._nsmap: str = self._root.nsmap

        if mode in ('r', 'a'):
            _validate_acbf(self._root.getroottree(), self._nsmap[None])

        self.styles: Styles = Styles(self)
        self.book_info: BookInfo = BookInfo(self)
        self.publisher_info: PublishInfo = PublishInfo(self)
        self.document_info: DocumentInfo = DocumentInfo(self)
        self.body: ACBFBody = ACBFBody(self)
        self.data: ACBFData = ACBFData(self)
        self.references: Dict[str, Dict[str, str]] = {}

        # References
        if self._root.find("references", namespaces=self._nsmap) is not None:
            for ref in self._root.findall("references/reference", namespaces=self._nsmap):
                pa = []
                for p in ref.findall("p", namespaces=self._nsmap):
                    text = re.sub(r'</?p[^>]*>', '', etree.tostring(p, encoding="utf-8").decode("utf-8").strip())
                    pa.append(text)
                self.references[ref.attrib["id"]] = {'_': '\n'.join(pa)}

    def _get_acbf_tree(self):
        """Converts the XML tree to a string with any modifications.

        Returns
        -------
        str
            ACBF book's XML data.
        """
        if self.mode == 'r':
            raise UnsupportedOperation("Book is not writeable.")

        ns = f"{{{self._nsmap[None]}}}"

        root = _get_root_template(self._nsmap)
        meta = root.find("meta-data", namespaces=self._nsmap)
        bd = root.find("body", namespaces=self._nsmap)

        def add_authors(section, au_list):
            for author in au_list:
                au = etree.SubElement(section, f"{ns}author", nsmap=self._nsmap)
                props = {x.replace('_', '-'): getattr(author, x)
                         for x in ("first_name", "last_name", "nickname")
                         if getattr(author, x) is not None}
                props.update({x.replace('_', '-'): getattr(author, x)
                              for x in ("middle_name", "home_page", "email")
                              if getattr(author, x) is not None}
                             )

                if author.activity is not None:
                    au.set("activity", author.activity.name)
                if author.lang is not None:
                    au.set("lang", author.lang)

                for k, v in props.items():
                    pr = etree.SubElement(au, ns + k, nsmap=self._nsmap)
                    pr.text = v

        #region Styles
        for st in self.styles.list_styles():
            if st == '_':
                style = etree.Element(f"{ns}style", nsmap=self._nsmap)
                meta.addprevious(style)
                style.text = self.styles['_'].decode("utf-8")
                if self.styles.types['_'] is not None:
                    style.set("type", self.styles.types['_'])
            else:
                sub = f'type="{self.styles.types[st]}" ' if self.styles.types[st] is not None else ''
                style = etree.ProcessingInstruction("xml-stylesheet", f'{sub}href="{st}"')
                root.addprevious(style)

        #endregion

        #region Book Info
        b_info = meta.find("book-info", namespaces=self._nsmap)

        # Authors
        add_authors(b_info, self.book_info.authors)

        # Titles
        for lang, title in self.book_info.book_title.items():
            ti = etree.SubElement(b_info, f"{ns}book-title", nsmap=self._nsmap)
            if lang != '_':
                ti.set("lang", lang)
            ti.text = title

        # Genres
        for genre, match in self.book_info.genres.items():
            gn = etree.SubElement(b_info, f"{ns}genre", nsmap=self._nsmap)
            gn.text = genre.name
            if match is not None:
                if 0 <= match <= 100:
                    gn.set("match", str(match))
                else:
                    raise ValueError(f"book_info.genre `match={match}`. Value must be from 0 to 100.")

        # Annotations
        for lang, annotation in self.book_info.annotations.items():
            an = etree.SubElement(b_info, f"{ns}annotation", nsmap=self._nsmap)
            if lang != '_':
                an.set("lang", lang)
            for para in annotation.splitlines():
                p = etree.SubElement(an, f"{ns}p", nsmap=self._nsmap)
                p.text = para

        # Cover Page (Filled in body section)
        etree.SubElement(b_info, f"{ns}coverpage", nsmap=self._nsmap)

        # --- Optional ---
        # Language Layers
        if len(self.book_info.languages) > 0:
            ll = etree.SubElement(b_info, f"{ns}languages", nsmap=self._nsmap)
            for layer in self.book_info.languages:
                etree.SubElement(ll, f"{ns}text-layer", lang=layer.lang, show=str(layer.show).lower(),
                                 nsmap=self._nsmap)

        # Characters
        if len(self.book_info.characters) > 0:
            ch = etree.SubElement(b_info, f"{ns}characters", nsmap=self._nsmap)
            for name in self.book_info.characters:
                nm = etree.SubElement(ch, f"{ns}name", nsmap=self._nsmap)
                nm.text = name

        # Keywords
        for lang, kwords in self.book_info.keywords.items():
            kw = etree.SubElement(b_info, f"{ns}keywords", nsmap=self._nsmap)
            if lang != '_':
                kw.set("lang", lang)
            kw.text = ", ".join(kwords)

        # Series
        for title, series in self.book_info.series.items():
            seq = etree.SubElement(b_info, f"{ns}sequence", title=title, nsmap=self._nsmap)
            seq.text = str(series.sequence)
            if series.volume is not None:
                seq.set("volume", str(series.volume))

        # Content Rating
        for type, rating in self.book_info.content_rating.items():
            cr = etree.SubElement(b_info, f"{ns}content-rating", type=type, nsmap=self._nsmap)
            cr.text = rating

        # Database Reference
        for dbref in self.book_info.database_ref:
            db = etree.SubElement(b_info, f"{ns}databaseref", dbname=dbref.dbname, nsmap=self._nsmap)
            db.text = dbref.reference
            if dbref.type is not None:
                db.set("type", dbref.type)

        #endregion

        #region Publisher Info
        p_info = meta.find("publish-info", namespaces=self._nsmap)

        p_info.find("publisher", namespaces=self._nsmap).text = self.publisher_info.publisher

        p_info.find("publish-date", namespaces=self._nsmap).text = self.publisher_info.publish_date
        if self.publisher_info.publish_date_value is not None:
            p_info.find("publish-date", namespaces=self._nsmap).set("value",
                                                                    self.publisher_info.publish_date_value.isoformat())

        if self.publisher_info.publish_city is not None:
            city = etree.SubElement(p_info, f"{ns}city", nsmap=self._nsmap)
            city.text = self.publisher_info.publish_city

        if self.publisher_info.isbn is not None:
            isbn = etree.SubElement(p_info, f"{ns}isbn", nsmap=self._nsmap)
            isbn.text = self.publisher_info.isbn

        if self.publisher_info.license is not None:
            license = etree.SubElement(p_info, f"{ns}license", nsmap=self._nsmap)
            license.text = self.publisher_info.license

        #endregion

        #region Document Info
        d_info = meta.find("document-info", namespaces=self._nsmap)

        add_authors(d_info, self.document_info.authors)

        d_info.find("creation-date", namespaces=self._nsmap).text = self.document_info.creation_date
        if self.document_info.creation_date_value is not None:
            d_info.find("creation-date", namespaces=self._nsmap).set("value",
                                                                     self.document_info.creation_date_value.isoformat())

        if self.document_info.source is not None:
            source = etree.SubElement(d_info, f"{ns}source", nsmap=self._nsmap)
            for para in self.document_info.source.splitlines():
                p = etree.SubElement(source, f"{ns}p", nsmap=self._nsmap)
                p.text = para

        if self.document_info.document_id is not None:
            id = etree.SubElement(d_info, f"{ns}id", nsmap=self._nsmap)
            id.text = self.document_info.document_id

        if self.document_info.document_version is not None:
            version = etree.SubElement(d_info, f"{ns}version", nsmap=self._nsmap)
            version.text = self.document_info.document_version

        if len(self.document_info.document_history) > 0:
            hst = etree.SubElement(d_info, f"{ns}history", nsmap=self._nsmap)
            for entry in self.document_info.document_history:
                p = etree.SubElement(hst, f"{ns}p", nsmap=self._nsmap)
                p.text = entry

        #endregion

        #region Body
        if self.body.bgcolor is not None:
            bd.set("bgcolor", self.body.bgcolor)

        pages = self.body.pages.copy()
        pages.insert(0, self.book_info.coverpage)
        for page in pages:
            if page.is_coverpage:
                pg = b_info.find("coverpage", namespaces=self._nsmap)
            else:
                pg = etree.SubElement(bd, f"{ns}page", nsmap=self._nsmap)
                if page.bgcolor is not None:
                    pg.set("bgcolor", page.bgcolor)
                if page.transition is not None:
                    pg.set("transition", page.transition.name)

                for lang, title in page.title.items():
                    ti = etree.SubElement(pg, f"{ns}title", nsmap=self._nsmap)
                    if lang != '_':
                        ti.set("lang", lang)
                    ti.text = title

            etree.SubElement(pg, f"{ns}image", href=page.image_ref, nsmap=self._nsmap)

            for lang, tx_layer in page.text_layers.items():
                tl = etree.SubElement(pg, f"{ns}text-layer", lang=lang, nsmap=self._nsmap)
                if tx_layer.bgcolor is not None:
                    tl.set("bgcolor", tx_layer.bgcolor)

                for tx_area in tx_layer.text_areas:
                    ta = etree.SubElement(tl, f"{ns}text-area", points=helpers.vec_to_pts(tx_area.points),
                                          nsmap=self._nsmap)
                    ta.extend(helpers.para_to_tree(tx_area.text, self._nsmap))

                    for i in ("bgcolor", "inverted", "transparent"):
                        if getattr(tx_area, i) is not None:
                            ta.set(i, str(getattr(tx_area, i)).lower())

                    if tx_area.rotation is not None:
                        ta.set("text-rotation", str(tx_area.rotation))

                    if tx_area.type is not None:
                        ta.set("type", tx_area.type.name)

            for frame in page.frames:
                fr = etree.SubElement(pg, f"{ns}frame", points=helpers.vec_to_pts(frame.points), nsmap=self._nsmap)
                if frame.bgcolor is not None:
                    fr.set("bgcolor", frame.bgcolor)

            for jump in page.jumps:
                etree.SubElement(pg, f"{ns}jump", page=str(jump.target), points=helpers.vec_to_pts(jump.points),
                                 nsmap=self._nsmap)

        #endregion

        #region Data
        if len(self.data) > 0:
            dt = etree.SubElement(root, f"{ns}data", nsmap=self._nsmap)

            for file in self.data.list_files():
                data = self.data[file]
                bn = etree.SubElement(dt, f"{ns}binary", attrib={"id": data.id, "content-type": data.type},
                                      nsmap=self._nsmap)
                bn.text = data._base64data
        #endregion

        #region References
        if len(self.references) > 0:
            refs = etree.SubElement(root, f"{ns}references", nsmap=self._nsmap)

            for id, reference in self.references.items():
                reference = reference['_']
                ref = etree.SubElement(refs, f"{ns}reference", id=id, nsmap=self._nsmap)
                for r in reference.splitlines():
                    p = f"<p>{r}</p>"
                    p_element = etree.fromstring(bytes(p, encoding="utf-8"))
                    for i in list(p_element.iter()):
                        i.tag = '{' + self._nsmap[None] + '}' + i.tag
                    ref.append(p_element)

        #endregion

        return root.getroottree()

    def create_placeholders(self):
        """Creates the minimum required values for the book to follow the schema. This means creating an empty page if
        there are no pages.
        """
        if len(self.body.pages) == 0:
            self.body.append_page('')

    def get_acbf_xml(self) -> str:
        """Get the XML tree of the ACBF book.

        Returns
        -------
        str
            The XML content of the ACBF book.
        """
        return etree.tostring(self._get_acbf_tree(),
                              encoding="utf-8",
                              xml_declaration=True,
                              pretty_print=True
                              ).decode("utf-8")

    def make_archive(self, archive_type: str = "Zip"):
        """Convert a plain ACBF XML book to an archive format.

        Parameters
        ----------
        archive_type : str, default="Zip"
            The type of archive to create. Allowed values are listed at
            :class:`ArchiveTypes <libacbf.constants.ArchiveTypes>`.

        Raises
        ------
        AttributeError (Book is already an archive of type ``{archive.type}``.)
            Raised when book is already an archive.
        """
        archive_type = consts.ArchiveTypes[archive_type]

        if self.archive is not None:
            raise AttributeError(f"Book is already an archive of type `{self.archive.type.name}`.")

        helpers.check_write(self)

        if archive_type == consts.ArchiveTypes.Rar:
            raise EditRARArchiveError

        if archive_type == consts.ArchiveTypes.Zip:
            with ZipFile(self._source, 'w') as _:
                pass
        elif archive_type == consts.ArchiveTypes.SevenZip:
            with SevenZipFile(self._source, 'w') as _:
                pass
        elif archive_type == consts.ArchiveTypes.Tar:
            with tar.open(self._source, 'w') as _:
                pass

        self.archive = ArchiveReader(self._source, 'w')
        name = self.book_path.stem + ".acbf" if self.book_path is not None else "book.acbf"
        self.archive.write(self.get_acbf_xml().encode("utf-8"), name)

    def close(self):
        """Saves and closes the book and closes the archive if it exists. Metadata and embedded data can still be read.
        Use ``ACBFBook.is_open`` to check if file is open.
        """
        if self.mode != 'r':
            _validate_acbf(self._get_acbf_tree(), self._nsmap[None])

            if self.archive is None:
                if self.book_path is not None:
                    with open(self._source, 'w') as book:
                        book.write(self.get_acbf_xml())
                else:
                    self._source.write(self.get_acbf_xml())
            else:
                self.archive.write(self.get_acbf_xml().encode("utf-8"), self.archive._get_acbf_file())

        self.mode = 'r'
        self.is_open = False

        if self.archive is not None:
            self.archive.close()

    def __repr__(self):
        if self.is_open:
            return object.__repr__(self).replace("libacbf.libacbf.ACBFBook", "libacbf.ACBFBook")
        else:
            return "<libacbf.ACBFBook [Closed]>"

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is not None:
            self.mode = 'r'
            self.is_open = False

            if self.archive is not None:
                self.archive.close()
        else:
            self.close()


class BookInfo:
    """Metadata about the book itself.

    See Also
    --------
    `Book-Info section <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Book-info_section>`_.

    Attributes
    ----------
    authors : List[Author]
        A list of :class:`Author <libacbf.metadata.Author>` objects.

    book_title : Dict[str, str]
        A dictionary with standard language codes as keys and titles as values. Key is ``'_'`` if no language is
        defined. ::

            {
                "_": "book title without language",
                "en": "English title",
                "en_GB": "English (UK) title",
                "en_US": "English (US) title"
            }

    genres : Dict[Genres, int | None]
        A dictionary with keys being a value from :class:`constants.Genres <libacbf.constants.Genres>` Enum and values
        being integers with the match value or ``None``. See :meth:`get_match()`.

    annotations : Dict[str, str]
        A short summary describing the book.

        It is a dictionary with keys being standard language codes or ``'_'`` if no language is defined and values
        being multiline strings.

    coverpage : Page
        It is the same as :class:`body.Page <libacbf.body.Page>` except it does not have
        :attr:`body.Page.title <libacbf.body.Page.title>`, :attr:`body.Page.bgcolor <libacbf.body.Page.bgcolor>`
        and :attr:`body.Page.transition <libacbf.body.Page.transition>`.

    languages : List[LanguageLayer], optional
        It represents all :class:`body.TextLayer <libacbf.body.TextLayer>` objects of the book.

        A list of :class:`LanguageLayer <libacbf.metadata.LanguageLayer>` objects.

    characters : List[str], optional
        List of (main) characters that appear in the book.

    keywords: Dict[str, Set[str]], optional
        For use by search engines.

        A dictionary with keys as standard language codes or ``'_'`` if no language is defined. Values are a set of
        lowercase keywords.

    series: Dict[str, Series], optional
        Contains the sequence and number if particular comic book is part of a series.

        A dictionary with keys as the title of the series and values as :class:`Series <libacbf.metadata.Series>`
        objects.

    content_rating: Dict[str, str], optional
        Content rating of the book based on age appropriateness and trigger warnings.

        It is a dictionary with the keys being the rating system and values being the rating. ::

            {
                "Age Rating": "16+",
                "DC Comics rating system": "T+",
                "Marvel Comics rating system": "PARENTAL ADVISORY"
            }

    database_ref : List[DBRef], optional
        References to a record in a comic book database (eg: GCD, MAL).

        A list of :class:`DBRef <libacbf.metadata.DBRef>` objects.
    """

    def __init__(self, book: ACBFBook):
        self._book = book
        nsmap = book._nsmap
        info = book._root.find("meta-data/book-info", namespaces=nsmap)

        self.authors: List[metadata.Author] = []
        self.book_title: Dict[str, str] = {}
        self.genres: Dict[consts.Genres, Optional[int]] = {}
        self.annotations: Dict[str, str] = {}
        self.coverpage: libacbf.body.Page = None

        # --- Optional ---
        self.languages: List[metadata.LanguageLayer] = []
        self.characters: List[str] = []
        self.keywords: Dict[str, Set[str]] = {}
        self.series: Dict[str, metadata.Series] = {}
        self.content_rating: Dict[str, str] = {}
        self.database_ref: List[metadata.DBRef] = []

        #region Fill values

        # Author
        self.authors.extend(
            _update_authors(
                info.findall("author", namespaces=nsmap),
                nsmap
                )
            )

        # Titles
        for title in info.findall("book-title", namespaces=nsmap):
            lang = '_'
            if "lang" in title.keys():
                lang = langcodes.standardize_tag(title.attrib["lang"])

            self.book_title[lang] = title.text

        # Genres
        for genre in info.findall("genre", namespaces=nsmap):
            gn = consts.Genres[genre.text]
            self.genres[gn] = None
            if "match" in genre.keys():
                self.genres[gn] = int(genre.attrib["match"])

        # Annotations
        for an in info.findall("annotation", namespaces=nsmap):
            p = []
            for i in an.findall('p', namespaces=nsmap):
                p.append(i.text)
            p = '\n'.join(p)

            lang = '_'
            if "lang" in an.keys():
                lang = langcodes.standardize_tag(an.attrib["lang"])
            self.annotations[lang] = p

        # Cover Page
        cpage = info.find("coverpage", namespaces=nsmap)
        image_ref = ''
        if cpage is not None:
            image_ref = cpage.find("image", namespaces=nsmap).attrib["href"]
        self.coverpage = libacbf.body.Page(image_ref, book, coverpage=True)
        if cpage is not None:
            _fill_page(cpage, self.coverpage, nsmap, self._book)

        # --- Optional ---

        # Languages
        if info.find("languages", namespaces=nsmap) is not None:
            text_layers = info.findall("languages/text-layer", namespaces=nsmap)
            for layer in text_layers:
                lang = langcodes.standardize_tag(layer.attrib["lang"])
                show = bool(distutils.util.strtobool(layer.attrib["show"]))
                self.languages.append(metadata.LanguageLayer(lang, show))

        # Characters
        if info.find("characters", namespaces=nsmap) is not None:
            for c in info.findall("characters/name", namespaces=nsmap):
                self.characters.append(c.text)

        # Keywords
        for k in info.findall("keywords", namespaces=nsmap):
            if k.text is not None:
                lang = '_'
                if "lang" in k.keys():
                    lang = langcodes.standardize_tag(k.attrib["lang"])
                self.keywords[lang] = {x.lower() for x in re.split(", |,", k.text)}

        # Series
        for se in info.findall("sequence", namespaces=nsmap):
            ser = metadata.Series(se.text)
            if "volume" in se.keys():
                ser.volume = se.attrib["volume"]
            self.series[se.attrib["title"]] = ser

        # Content Rating
        for rt in info.findall("content-rating", namespaces=nsmap):
            self.content_rating[rt.attrib["type"]] = rt.text

        # Database Reference
        for db in info.findall("databaseref", namespaces=nsmap):
            dbref = metadata.DBRef(db.attrib["dbname"], db.text)
            if "type" in db.keys():
                dbref.type = db.attrib["type"]
            self.database_ref.append(dbref)

        #endregion

    @helpers.check_book
    def add_author(self, *names: str, first_name=None, last_name=None, nickname=None) -> metadata.Author:
        """Add an Author to the book info. Usage is the same as :class:`Author <libacbf.metadata.Author>`.

        Returns
        -------
        Author
            The created Author object.
        """
        author = metadata.Author(*names, first_name=first_name, last_name=last_name, nickname=nickname)
        self.authors.append(author)
        return author

    def get_genre_match(self, genre: str) -> int:
        """Get match value of genre by string.
        """
        return self.genres[consts.Genres[genre]]

    @helpers.check_book
    def edit_genre(self, genre: str, match: Optional[int] = '_'):
        """Edit a genre by string. Add it if it doesn't exist.

        Parameters
        ----------
        genre : str
            See :class:`constants.Genres <libacbf.constants.Genres>` enum for a list of possible values.

        match : int | None, optional
            Set the match percentage of the genre. If ``None``, removes the match value.
        """
        if match != '_' and (match < 0 or match > 100):
            raise ValueError("`match` must be an integer from 0 to 100.")

        genre = consts.Genres[genre]

        if match == '_':
            if genre in self.genres:
                match = self.genres[genre]
            else:
                match = None

        self.genres[genre] = match

    @helpers.check_book
    def pop_genre(self, genre: str) -> Optional[int]:
        """Pop a genre by string.

        Returns
        -------
        int | None
            The match value of the genre.
        """

        return self.genres.pop(consts.Genres[genre])

    @helpers.check_book
    def add_language(self, lang: str, show: bool):
        """Add a language layer to the book. Usage is the same as
        :class:`LanguageLayer <libacbf.metadata.LanguageLayer>`.
        """
        self.languages.append(metadata.LanguageLayer(lang, show))

    @helpers.check_book
    def add_series(self, title: str, sequence: str, volume: Optional[str] = None):
        """Add a series that the book belongs to. ``title`` is the key and usage for value is the same as
        :class:`Series <libacbf.metadata.Series>`.
        """
        self.series[title] = metadata.Series(sequence, volume)

    @helpers.check_book
    def add_dbref(self, dbname: str, ref: str, type: Optional[str] = None):
        """Add a database reference to the book. Usage is the same as :class:`DBRef <libacbf.metadata.DBRef>`.
        """
        self.database_ref.append(metadata.DBRef(dbname, ref, type))


class PublishInfo:
    """Metadata about the book's publisher.

    See Also
    --------
    `Publish-Info section <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Publish-Info_Section>`_.

    Attributes
    ----------
    publisher : str
        Name of the publisher.

    publish_date : str
        Date when the book was published as a human readable string.

    publish_date_value : datetime.date, optional
        Date when the book was published.

    publish_city : str, optional
        City where the book was published.

    isbn : str, optional
        International Standard Book Number.

    license : str, optional
        The license that the book is under.
    """

    def __init__(self, book: ACBFBook):
        self._book = book
        nsmap = book._nsmap
        info = book._root.find("meta-data/publish-info", namespaces=nsmap)

        self.publisher: str = info.find("publisher", namespaces=nsmap).text
        self.publish_date: str = info.find("publish-date", namespaces=nsmap).text

        # --- Optional ---
        self.publish_date_value: Optional[date] = None
        self.publish_city: Optional[str] = None
        self.isbn: Optional[str] = None
        self.license: Optional[str] = None

        #region Fill values

        # Date
        if "value" in info.find("publish-date", namespaces=nsmap).keys():
            self.publish_date_value = date.fromisoformat(
                info.find("publish-date", namespaces=nsmap).attrib["value"])

        # City
        if info.find("city", namespaces=nsmap) is not None:
            self.publish_city = info.find("city", namespaces=nsmap).text

        # ISBN
        if info.find("isbn", namespaces=nsmap) is not None:
            self.isbn = info.find("isbn", namespaces=nsmap).text

        # License
        if info.find("license", namespaces=nsmap) is not None:
            self.license = info.find("license", namespaces=nsmap).text

        #endregion

    @helpers.check_book
    def set_date(self, date: Union[str, date], include_date: bool = True):
        """Edit the date the book was published.

        Parameters
        ----------
        date : str | datetime.date
            Date to set to.

        include_date : bool, default=True
            Whether to also set :attr:`publish_date_value`. Passing ``False`` will set it to ``None``.
        """
        _edit_date(self, "publish_date", "publish_date_value", date, include_date)


class DocumentInfo:
    """Metadata about the ACBF file itself.

    See Also
    --------
    `Document-Info section <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Document-Info_Section>`_.

    Attributes
    ----------
    authors : List[Author]
        Authors of the ACBF file as a list of :class:`Author <libacbf.metadata.Author>` objects.

    creation_date : str
        Date when the ACBF file was created as a human readable string.

    creation_date_value : datetime.date, optional
        Date when the ACBF file was created.

    source : str, optional
        A multiline string with information if this book is a derivative of another work. May
        contain URL and other source descriptions.

    document_id : str, optional
        Unique Document ID. Used to distinctly define ACBF files for cataloguing.

    document_version : str, optional
        Version of ACBF file.

    document_history : List[str], optional
        Change history of the ACBF file with change information in a list of strings.
    """

    def __init__(self, book: ACBFBook):
        self._book = book
        nsmap = book._nsmap
        info = book._root.find("meta-data/document-info", namespaces=nsmap)

        self.authors: List[metadata.Author] = []
        self.creation_date: str = info.find("creation-date", namespaces=nsmap).text

        # --- Optional ---
        self.creation_date_value: Optional[date] = None
        self.source: Optional[str] = None
        self.document_id: Optional[str] = None
        self.document_version: Optional[str] = None
        self.document_history: List[str] = []

        #region Fill values

        # Author
        self.authors.extend(
            _update_authors(
                info.findall("author", namespaces=nsmap),
                nsmap
                )
            )

        # Date
        if "value" in info.find("creation-date", namespaces=nsmap).keys():
            self.creation_date_value = date.fromisoformat(
                info.find("creation-date", namespaces=nsmap).attrib["value"])

        # Source
        if info.find("source", namespaces=nsmap) is not None:
            p = []
            for line in info.findall("source/p", namespaces=nsmap):
                p.append(line.text)
            self.source = '\n'.join(p)

        # ID
        if info.find("id", namespaces=nsmap) is not None:
            self.document_id = info.find("id", namespaces=nsmap).text

        # Version
        if info.find("version", namespaces=nsmap) is not None:
            self.document_version = info.find("version", namespaces=nsmap).text

        # History
        for item in info.findall("history/p", namespaces=nsmap):
            self.document_history.append(item.text)

        #endregion

    @helpers.check_book
    def add_author(self, *names: str, first_name=None, last_name=None, nickname=None) -> metadata.Author:
        """Add an Author to the document info. Usage is the same as :class:`Author <libacbf.metadata.Author>`.

        Returns
        -------
        Author
            The created Author object.
        """
        author = metadata.Author(*names, first_name=first_name, last_name=last_name, nickname=nickname)
        self.authors.append(author)
        return author

    @helpers.check_book
    def set_date(self, date: Union[str, date], include_date: bool = True):
        """Edit the date the ACBF file was created.

        Parameters
        ----------
        date : str | datetime.date
            Date to set to.

        include_date : bool, default=True
            Whether to also set :attr:`creation_date_value`. Passing ``False`` will set it to ``None``.
        """
        _edit_date(self, "creation_date", "creation_date_value", date, include_date)


class ACBFBody:
    """Body section contains the definition of individual book pages and text layers, frames and jumps inside those
    pages.

    See Also
    --------
    `Body Section Definition <https://acbf.fandom.com/wiki/Body_Section_Definition>`_.

    Attributes
    ----------
    pages : List[Page]
        A list of :class:`Page <libacbf.body.Page>` objects in the order they should be displayed in.

    bgcolor : str, optional
        Defines a background colour for the whole book. Can be overridden by ``bgcolor`` in pages,
        text layers, text areas and frames.
    """

    def __init__(self, book: ACBFBook):
        self._book = book
        nsmap = book._nsmap
        body = book._root.find("body", namespaces=nsmap)

        self.pages: List[libacbf.body.Page] = []

        # --- Optional ---
        self.bgcolor: Optional[str] = None

        #region Fill values

        # Background Colour
        if "bgcolor" in body.keys():
            self.bgcolor = body.attrib["bgcolor"]

        # Pages
        for pg in body.findall("page", namespaces=nsmap):
            img_ref = pg.find("image", namespaces=nsmap).attrib["href"]
            page = libacbf.body.Page(img_ref, book)

            if "bgcolor" in pg.keys():
                page.bgcolor = pg.attrib["bgcolor"]

            if "transition" in pg.keys():
                page.transition = consts.PageTransitions[pg.attrib["transition"]]

            for title in pg.findall("title", namespaces=nsmap):
                lang = '_'
                if "lang" in title.keys():
                    lang = langcodes.standardize_tag(title.attrib["lang"])
                page.title[lang] = title.text

            _fill_page(pg, page, nsmap, self._book)

            self.pages.append(page)

        #endregion

    @helpers.check_book
    def insert_page(self, index: int, image_ref: str) -> libacbf.body.Page:
        """Insert a new Page object at the index.

        Parameters
        ----------
        index : int
            Index of new page.

        image_ref : str
            Value to set for the image reference. See :attr:`Page.image_ref <libacbf.body.Page.image_ref>` for
            information on how to format it.

        Returns
        -------
        Page
            The created Page object.
        """
        self.pages.insert(index, libacbf.body.Page(image_ref, self._book))
        return self.pages[index]

    @helpers.check_book
    def append_page(self, image_ref: str) -> libacbf.body.Page:
        """Append a new Page object to the body.

        Parameters
        ----------
        image_ref : str
            Value to set for the image reference. See :attr:`Page.image_ref <libacbf.body.Page.image_ref>` for
            information on how to format it.

        Returns
        -------
        Page
            The created Page object.
        """
        page = libacbf.body.Page(image_ref, self._book)
        self.pages.append(page)
        return page


class ACBFData:
    """Get any binary data embedded in the ACBF file or write data to archive or embed data in ACBF.

    See Also
    --------
    `Data Section Definition <https://acbf.fandom.com/wiki/Data_Section_Definition>`_.

    Returns
    -------
    BookData
        A file as a :class:`BookData <libacbf.bookdata.BookData>` object.

    Raises
    ------
    FileNotFoundError
        Raised if file is not found embedded in the ACBF file.

    Examples
    --------
    To get a file embedded in the ACBF file::

        from libacbf import ACBFBook

        with ACBFBook("path/to/book.cbz") as book:
            image = book.data["image.png"]
            font = book.data["font.ttf"]
    """

    def __init__(self, book: ACBFBook):
        self._book = book
        self._files: Dict[str, BookData] = {}
        nsmap = book._nsmap

        for i in book._root.findall("data/binary", namespaces=nsmap):
            new_data = BookData(i.attrib["id"], i.attrib["content-type"], i.text)
            self._files[i.attrib["id"]] = new_data

    def list_files(self) -> Set[str]:
        """Returns a list of all the names of the files embedded in the ACBF file. May be images, fonts etc.

        Returns
        -------
        Set[str]
            A set of file names.
        """
        return set(self._files.keys())

    @helpers.check_book
    def add_data(self, target: Union[str, Path, bytes], name: str = None, embed: bool = False):
        """Add or embed data into the book.

        Parameters
        ----------
        target : str | Path | bytes
            Path to file to be added or data as bytes.

        name : str, optional
            Name to assign to file after writing. Defaults to name part of target. Required if ``target`` is bytes.

        embed : bool, default=False
            Whether to embed the file in the ACBF XML. Cannot be ``False`` if book is not an archive type. Use
            :meth:`ACBFBook.make_archive(...) <libacbf.ACBFBook.make_archive()>` to convert the book to an archive.
        """
        if self._book.archive is None and not embed:
            raise AttributeError("Book is not an archive type. Write data with `embed = True` or use "
                                 "`ACBFBook.make_archive(...)` to convert the book to an archive.")

        if isinstance(target, str):
            target = Path(target).resolve(True)

        if isinstance(target, bytes) and name is None:
            raise ValueError("`name` is required if `target` is bytes.")

        name = target.name if name is None else name

        if embed:
            if isinstance(target, bytes):
                contents = target
            else:
                with open(target, 'rb') as file:
                    contents = file.read()
            type = magic.from_buffer(contents, True)
            data = b64encode(contents).decode("utf-8")

            self._files[name] = BookData(name, type, data)
        else:
            self._book.archive.write(target, name)

    @helpers.check_book
    def remove_data(self, target: Union[str, Path], embed: bool = False):
        """Remove file at target in the archive. If ``embed`` is true, removes from embedded files.

        Parameters
        ----------
        target : str | Path
            Path to file in archive or id of embedded file.

        embed : bool, default=False
            Whether to check for file in archive or embedded in ACBF XML. Must be true if book is plain ACBF XML.
        """
        if self._book.archive is None and not embed:
            raise AttributeError("Book is not an archive type. Write data with `embed = True` or use "
                                 "`ACBFBook.make_archive(...)` to convert the book to an archive.")

        if embed:
            if not isinstance(target, str):
                target = str(target)
            self._files.pop(target)
        else:
            if isinstance(target, str):
                target = Path(target)
            self._book.archive.delete(target)

    def __len__(self):
        return len(self._files.keys())

    def __getitem__(self, key: str):
        if key not in self.list_files():
            raise FileNotFoundError(f"`{key}` not found embedded in book.")
        return self._files[key]


class Styles:
    """Stylesheets to be used in the book.

    See Also
    --------
    `Stylesheet Declaration <https://acbf.fandom.com/wiki/Stylesheet_Declaration>`_.

    Returns
    -------
    bytes
        Stylesheet data.

    Examples
    --------
    To get stylesheets ::

        from libacbf import ACBFBook

        with ACBFBook("path/to/book.cbz") as book:
            style1 = book.styles["style1.css"]  # Style referenced at the top of the ACBF XML.
            embedded_style = book.styles['_']  # Returns the stylesheet embedded in ACBF XML.

    Attributes
    ----------
    types : Dict[str, str | None]
        A dictionary with keys being the style name (or ``'_'``) and values being the type or ``None`` if not specified.
    """

    def __init__(self, book: ACBFBook):
        self._book = book
        nsmap = book._nsmap

        self._styles: Dict[str, Optional[bytes]] = {}
        self.types: Dict[str, Optional[str]] = {}

        for i in book._root.xpath("//processing-instruction('xml-stylesheet')"):
            self.types[i.attrib["href"]] = i.attrib["type"] if "type" in i.attrib.keys() else None
            self._styles[i.attrib["href"]] = None
        embedded = book._root.find("style", namespaces=nsmap)
        if embedded is not None:
            self._styles['_'] = book._root.find("style", namespaces=nsmap).text.strip().encode("utf-8")
            self.types['_'] = embedded.attrib["type"] if "type" in embedded.keys() else None

    def list_styles(self) -> Set[str]:
        """All the stylesheets referenced by the ACBF XML.

        Returns
        -------
        Set[str]
            Referenced stylesheets.
        """
        return set(self.types.keys())

    @helpers.check_book
    def edit_style(self, stylesheet: Union[str, Path, bytes], style_name: str = None, type: str = "text/css",
                   embed: bool = False):
        """Writes or overwrites file in book with referenced stylesheet.

        Parameters
        ----------
        stylesheet : str | Path | bytes
            Path to stylesheet or stylesheet as bytes.

        style_name : str, optional
            Name of stylesheet after being written. Defaults to name part of ``stylesheet_ref``. If it is ``'_'``,
            writes stylesheet to style tag of ACBF XML. Required if ``stylesheet`` is bytes.

        type : str, default="text/css"
            Mime Type of stylesheet. Defaults to CSS but can be others (like SASS).

        embed : bool, default=False
            Whether to embed stylesheet in the data section of the book. This is ignored if ``style_name`` is ``'_'``.
            Must be True if book is plain ACBF XML.
            Use :meth:`ACBFBook.make_archive(...) <libacbf.ACBFBook.make_archive()>` to convert the book to an archive.
        """
        if isinstance(stylesheet, str):
            stylesheet = Path(stylesheet)

        if isinstance(stylesheet, bytes) and style_name is None:
            raise ValueError("`style_name` is required if `stylesheet` is bytes.")

        if style_name is None:
            style_name = stylesheet.name

        if style_name == '_':
            if isinstance(stylesheet, bytes):
                self._styles['_'] = stylesheet
            else:
                with open(stylesheet, "rb") as css:
                    self._styles['_'] = css.read()
            self.types['_'] = type
        else:
            self._book.data.add_data(stylesheet, style_name, embed)
            self._styles[style_name] = None
            self.types[style_name] = type

    @helpers.check_book
    def remove_style(self, style_name: str, embedded: bool = False):
        """Remove stylesheet from book.

        Parameters
        ----------
        style_name : str
            Stylesheet to remove. If it is ``'_'``, remove embedded stylesheet.

        embedded : bool, default=False
            Remove style from embedded data of book. Ignored if style_name is ``'_'``. Must be False if book is plain
            ACBF XML.
        """
        self._styles.pop(style_name)
        self.types.pop(style_name)
        if style_name != '_':
            self._book.data.remove_data(style_name, embedded)

    def __len__(self):
        len(self._styles.keys())

    def __getitem__(self, key: str):
        if key not in self.list_styles():
            raise FileNotFoundError(f"`{key}` style could not be found.")

        if self._styles[key] is None:
            if key in self._book.data.list_files():
                self._styles[key] = self._book.data[key].data
            elif self._book.archive is not None:
                self._styles[key] = self._book.archive.read(key)
            else:
                st_path = self._book.book_path.parent / Path(key)
                with open(str(st_path), "rb") as st:
                    self._styles[key] = st.read()

        return self._styles[key]
