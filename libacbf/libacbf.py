import os
import re
import warnings
import tempfile
import magic
import distutils.util
import dateutil.parser
import langcodes
from io import TextIOBase, UnsupportedOperation
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
import libacbf.metadata as meta
import libacbf.body as body
from libacbf.bookdata import BookData
from libacbf.archivereader import ArchiveReader
from libacbf.exceptions import InvalidBook, EditRARArchiveError


def _validate_acbf(tree, ns: str):
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


def _update_authors(author_items, nsmap) -> List[meta.Author]:
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

        author: meta.Author = meta.Author(first_name, last_name, nickname)

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


def _fill_page(pg, page, nsmap):
    for fr in pg.findall("frame", namespaces=nsmap):
        frame = body.Frame(helpers.pts_to_vec(fr.attrib["points"]))
        if "bgcolor" in fr.keys():
            frame.bgcolor = fr.attrib["bgcolor"]
        page.frames.append(frame)

    for jp in pg.findall("jump", namespaces=nsmap):
        jump = body.Jump(helpers.pts_to_vec(jp.attrib["points"]), int(jp.attrib["page"]))
        page.jumps.append(jump)

    # Text Layers
    for tl in pg.findall("text-layer", namespaces=nsmap):
        lang = langcodes.standardize_tag(tl.attrib["lang"])
        layer = body.TextLayer()
        page.text_layers[lang] = layer

        if "bgcolor" in tl.keys():
            layer.bgcolor = tl.attrib["bgcolor"]

        # Text Areas
        for ta in tl.findall("text-area", namespaces=nsmap):
            text = helpers.tree_to_para(ta, nsmap[None])
            pts = helpers.pts_to_vec(ta.attrib["points"])
            area = body.TextArea(text, pts)
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


def get_root_template(nsmap: Dict):
    """Get the lxml root tree for a basic ACBF book.

    Parameters
    ----------
    nsmap : dict
        Namespaces
    """
    root = etree.Element("ACBF", nsmap=nsmap)
    meta = etree.SubElement(root, "meta-data")
    root.append(etree.Element("body"))

    book_info = etree.SubElement(meta, "book-info")

    publish_info = etree.SubElement(meta, "publish-info")
    publish_info.append(etree.Element("publisher"))
    publish_info.append(etree.Element("publish-date"))

    document_info = etree.SubElement(meta, "document-info")
    document_info.append(etree.Element("creation-date"))

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

    return etree.tostring(get_root_template({None: ns}).getroottree(),
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

        You do not have to specify the type of archive unless you are creating a new one. The correct type will be
        determined regardless of this parameter's value. Use this when you want to create a new archive or if you are
        reading/writing/editing a plain ACBF book.

        Warnings
        --------
        You can only write data by embedding when this is ``None``.

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

    Warnings
    --------
    Never try to edit variables directly as you will not be editing the XML. Use the editing functions instead.

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
        See :class:`BookInfo <libacbf.metadata.BookInfo>` for more information.

    publisher_info : PublishInfo
        See :class:`PublishInfo <libacbf.metadata.PublishInfo>` for more information.

    document_info : DocumentInfo
        See :class:`DocumentInfo <libacbf.metadata.DocumentInfo>` for more information.

    body : ACBFBody
        See :class:`ACBFBody <libacbf.libacbf.ACBFBody>` for more information.

    data : ACBFData
        See :class:`ACBFData <libacbf.libacbf.ACBFData>` for more information.

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
        see :attr:`TextArea.paragraph <libacbf.body.TextArea.paragraph>`.

    styles : Styles
        See :class:`Styles <libacbf.libacbf.Styles>` for more information.

    book_path : pathlib.Path
        Absolute path to source file.

    archive : ArchiveReader | None
        Can be used to read archive directly if file is not plain ACBF. Use this if you want to read exactly what
        files the book contains but try to avoid directly writing files through ``ArchiveReader``.

        :attr:`ArchiveReader.archive <libacbf.archivereader.ArchiveReader.archive>` may be ``zipfile.ZipFile``,
        ``py7zr.SevenZipFile``, ``tarfile.TarFile`` or ``rarfile.RarFile``.
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

        archive_type = consts.ArchiveTypes[archive_type] if archive_type is not None else None
        is_text = archive_type is None
        if isinstance(file, TextIOBase):
            archive_type = None
            is_text = True

        if archive_type == consts.ArchiveTypes.Rar and mode != 'r':
            raise EditRARArchiveError

        arc_mode = mode

        def create_file():
            if not is_text:
                arc = None
                if archive_type == consts.ArchiveTypes.Zip:
                    arc = ZipFile(file, 'w')
                elif archive_type == consts.ArchiveTypes.SevenZip:
                    arc = SevenZipFile(file, 'w')
                elif archive_type == consts.ArchiveTypes.Tar:
                    arc = tar.open(file, 'w')

                name = self.book_path.stem + ".acbf" if self.book_path is not None else "book.acbf"
                self.archive = ArchiveReader(arc, arc_mode)
                acbf_path = Path(tempfile.gettempdir()) / name
                with open(acbf_path, 'w') as xml:
                    xml.write(get_book_template())
                self.archive.write(acbf_path)
                self.archive.save(file)
                os.remove(acbf_path)
            else:
                if self.book_path is not None:
                    with open(str(self.book_path), 'w') as book:
                        book.write(get_book_template())
                else:
                    file.write(get_book_template())

        if mode in ('r', 'a'):
            if self.book_path is not None and not self.book_path.is_file():
                raise FileNotFoundError
            if mode == 'a' and not is_text:
                arc_mode = 'w'
                self.archive = ArchiveReader(file, arc_mode)
                if self.archive._get_acbf_file() is None:
                    name = "book.acbf"
                    if self.archive.filename is not None:
                        name = Path(self.archive.filename).with_suffix(".acbf")
                    acbf_path = Path(tempfile.gettempdir()) / name

                    with open(acbf_path, 'w') as xml:
                        xml.write(get_book_template())

                    self.archive.write(acbf_path)
                    self.archive.save(file)
                    os.remove(acbf_path)

        elif mode == 'x':
            if self.book_path is not None:
                if self.book_path.is_file():
                    raise FileExistsError
                else:
                    create_file()
            else:
                raise FileExistsError
            arc_mode = 'w'

        elif mode == 'w':
            create_file()

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
                with open(str(file), 'r') as book:
                    contents = book.read()

        if isinstance(contents, bytes):
            contents = contents.decode("utf-8")

        self._root = etree.fromstring(bytes(contents, "utf-8"))
        self._nsmap: str = self._root.nsmap

        if mode == 'r':
            _validate_acbf(self._root.getroottree(), self._nsmap[None])

        self.styles: Styles = Styles(self, str(contents))
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

    def get_acbf_xml(self) -> str:
        """Converts the XML tree to a string.

        Returns
        -------
        str
            ACBF book's XML data.
        """
        if self.mode == 'r':
            raise UnsupportedOperation("File is not writeable.")

        ns = self._nsmap
        root = get_root_template({None: re.sub(r'[{}]', '', ns)})
        meta = root.find("meta-data")
        body = root.find("body")

        #region Styles
        for st in self.styles.list_styles():
            if st == '_':
                style = etree.Element("style")
                root.find("meta-data").addprevious(style)
                if self.styles.types['_'] is not None:
                    style.set("type", self.styles.types['_'])
            else:
                sub = f'type="{self.styles.types[st]}" ' if self.styles.types[st] is not None else ''
                style = etree.ProcessingInstruction("xml-stylesheet", f'{sub}href="{st}"')
                root.addprevious(style)

        #endregion

        #region Book Info
        b_info = meta.find("book-info")

        def add_authors(section, au_list):
            for author in au_list:
                au = etree.SubElement(section, "author")
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
                    pr = etree.SubElement(au, k)
                    pr.text = str(v)

        # Authors
        add_authors(b_info, self.book_info.authors)

        # Titles
        for lang, title in self.book_info.book_title.items():
            ti = etree.SubElement(b_info, "book-title")
            if lang != '_':
                ti.set("lang", lang)
            ti.text = title

        # Genres
        for genre in self.book_info.genres.values():
            gn = etree.SubElement(b_info, "genre")
            gn.text = genre.genre.name
            if genre.match is not None:
                gn.set("match", genre.match)

        # Annotations
        for lang, annotation in self.book_info.annotations.items():
            an = etree.SubElement(b_info, "annotation")
            if lang != '_':
                an.set("lang", lang)
            for para in annotation.splitlines():
                p = etree.SubElement(an, 'p')
                p.text = para

        # Cover Page (Filled in body section)
        etree.SubElement(b_info, "coverpage")

        # --- Optional ---
        # Language Layers
        ll = etree.SubElement(b_info, "languages")
        for layer in self.book_info.languages:
            tl = etree.SubElement(ll, "text-layer", lang=layer.lang, show=layer.show)

        # Characters
        ch = etree.SubElement(b_info, "characters")
        for name in self.book_info.characters:
            nm = etree.SubElement(ch, "name")
            nm.text = name

        # Keywords
        for lang, kwords in self.book_info.keywords.items():
            kw = etree.SubElement(b_info, "keywords")
            if lang != '_':
                kw.set("lang", lang)
            kw.text = ", ".join(kwords)

        # Series
        for series in self.book_info.series.values():
            seq = etree.SubElement(b_info, "sequence", title=series.title)
            seq.text = series.sequence
            if series.volume is not None:
                seq.set("volume", series.volume)

        # Content Rating
        for type, rating in self.book_info.content_rating.items():
            cr = etree.SubElement(b_info, "content-rating")
            cr.text = rating
            if type != '_':
                cr.set("type", type)

        # Database Reference
        for dbref in self.book_info.database_ref:
            db = etree.SubElement(b_info, "databaseref", dbname=dbref.dbname)
            db.text = dbref.reference
            if dbref.type is not None:
                db.set(dbref.type)

        #endregion

        #region Publisher Info
        p_info = meta.find("publish-info")

        p_info.find("publisher").text = self.publisher_info.publisher

        p_info.find("publish-date").text = self.publisher_info.publish_date
        if self.publisher_info.publish_date_value is not None:
            p_info.find("publish-date").set("value", self.publisher_info.publish_date_value.isoformat())

        city = etree.SubElement(p_info, "city")
        city.text = self.publisher_info.publish_city

        isbn = etree.SubElement(p_info, "isbn")
        isbn.text = self.publisher_info.isbn

        license = etree.SubElement(p_info, "license")
        license.text = self.publisher_info.license

        #endregion

        #region Document Info
        d_info = meta.find("document-info")

        add_authors(d_info, self.document_info.authors)

        d_info.find("creation-date").text = self.document_info.creation_date
        if self.document_info.creation_date_value is not None:
            d_info.find("creation-date").set("value", self.document_info.creation_date_value.isoformat())

        source = etree.SubElement(d_info, "source")
        source.text = self.document_info.source

        id = etree.SubElement(d_info, "id")
        id.text = self.document_info.document_id

        version = etree.SubElement(d_info, "version")
        version.text = self.document_info.document_version

        hst = etree.SubElement(d_info, "history")
        for entry in self.document_info.document_history:
            p = etree.SubElement(hst, 'p')
            p.text = entry

        #endregion

        #region Body
        if self.body.bgcolor is not None:
            body.set("bgcolor", self.body.bgcolor)

        for page in self.body.pages.copy().insert(0, self.book_info.coverpage):
            pg = None
            if page.is_coverpage:
                pg = b_info.find("coverpage")
            else:
                pg = etree.SubElement(body, "page")
                if page.bgcolor is not None:
                    pg.set("bgcolor", page.bgcolor)
                if page.transition is not None:
                    pg.set("transition", page.transition)

                for lang, title in page.title.items():
                    ti = etree.SubElement(pg, "title")
                    if lang != '_':
                        ti.set("lang", lang)
                    ti.text = title

            etree.SubElement(pg, "image", href=page.image_ref)

            for tx_layer in page.text_layers.values():
                tl = etree.SubElement(pg, "text-layer", lang=tx_layer.lang)
                if tx_layer.bgcolor is not None:
                    tl.set("bgcolor", tx_layer.bgcolor)

                for tx_area in tx_layer.text_areas:
                    ta = etree.SubElement(tl, "text-area", points=helpers.vec_to_pts(tx_area.points))
                    ta.extend(helpers.para_to_tree(tx_area.text, ns))

                    for i in ("bgcolor", "rotation"):
                        if getattr(tx_area, i) is not None:
                            ta.set(i, str(getattr(tx_area, i)))

                    for i in ("inverted", "transparent"):
                        if getattr(tx_area, i) is not None:
                            ta.set(i, str(getattr(tx_area, i)).lower())

                    if tx_area.type is not None:
                        ta.set("type", tx_area.type.name)

            for frame in page.frames:
                fr = etree.SubElement(pg, "frame", points=helpers.vec_to_pts(frame.points))
                if frame.bgcolor is not None:
                    fr.set("bgcolor", frame.bgcolor)

            for jump in page.jumps:
                jp = etree.SubElement(pg, "jump", page=jump.page, points=helpers.vec_to_pts(jump.points))

        #endregion

        #region Data
        if len(self.data) > 0:
            dt = etree.SubElement(root, "data")

            for file in self.data.list_files():
                data = self.data[file]
                bn = etree.SubElement(dt, "binary", attrib={"id": data.id, "content-type": data.type})
                bn.text = data._base64data
        #endregion

        #region References
        if len(self.references) > 0:
            refs = etree.SubElement(root, "references")

            for id, reference in self.references.items():
                reference = reference['_']
                ref = etree.SubElement(refs, "reference", id=id)
                for r in reference.splitlines():
                    p = f"<p>{r}</p>"
                    p_element = etree.fromstring(bytes(p, encoding="utf-8"))
                    for i in list(p_element.iter()):
                        i.tag = ns + i.tag
                    ref.append(p_element)

        #endregion

        _validate_acbf(root.getroottree(), self._nsmap[None])

        return etree.tostring(root.getroottree(),
                              encoding="utf-8",
                              xml_declaration=True,
                              pretty_print=True
                              ).decode("utf-8")

    def save(self, file: Union[str, Path, IO, None] = None, overwrite: bool = False):
        """Save to file.

        Parameters
        ----------
        file : str | Path | IO, optional
            Path to save to. Defaults to the original path/file.

        overwrite : bool, default=False
            Whether to overwrite if file already exists at path. ``False`` by default.
        """
        if self.mode == 'r':
            raise UnsupportedOperation("File is not writeable.")

        xml_data = self.get_acbf_xml()

        if isinstance(file, str):
            file = Path(file)

        if file is None:
            if self.book_path is not None:
                file = self.book_path
            else:
                file = self._source
        elif isinstance(file, Path):
            if file.is_file() and not overwrite:
                raise FileExistsError
            self.book_path = file.absolute()

        if self.archive is None:
            if isinstance(file, Path):
                with open(str(file), 'w') as book:
                    book.write(xml_data)
            else:
                file.write(xml_data)
        else:
            acbf_path = Path(tempfile.gettempdir()) / self.archive._get_acbf_file()
            with open(acbf_path, 'w') as xml:
                xml.write(xml_data)
            self.archive.write(acbf_path)
            self.archive.save(file)
            os.remove(acbf_path)

    def close(self):
        """Saves the book and closes the archive if it exists. Metadata and embedded data can still be read. Use
        ``ACBFBook.is_open`` to check if file is open.
        """
        if self.mode != 'r':
            self.save(overwrite=True)

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
        self.close()


class BookInfo:
    """Metadata about the book itself.

    See Also
    --------
    `Book-Info section <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Book-info_section>`_.

    Attributes
    ----------
    book : ACBFBook
        Book that the metadata belongs to.

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

    genres : Dict[str, Genre]
        A dictionary with keys being a string representation of :class:`constants.Genres <libacbf.constants.Genres>`
        Enum and values being :class:`Genre <libacbf.metadata.Genre>` objects.

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

        It is a dictionary with the keys being the rating system or ``'_'`` if not defined and values being the
        rating. ::

            {
                "_": "16+",
                "Age Rating": "15+",
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

        self.authors: List[meta.Author] = []
        self.book_title: Dict[str, str] = {}
        self.genres: Dict[consts.Genres, Optional[int]] = {}
        self.annotations: Dict[str, str] = {}
        self.coverpage: body.Page = None

        # --- Optional ---
        self.languages: List[meta.LanguageLayer] = []
        self.characters: List[str] = []
        self.keywords: Dict[str, Set[str]] = {}
        self.series: Dict[str, meta.Series] = {}
        self.content_rating: Dict[str, str] = {}
        self.database_ref: List[meta.DBRef] = []

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
        image_ref = cpage.find("image", namespaces=nsmap).attrib["href"]
        self.coverpage = body.Page(image_ref, book, coverpage=True)
        _fill_page(cpage, self.coverpage, nsmap)

        # --- Optional ---

        # Languages
        if info.find("languages", namespaces=nsmap) is not None:
            text_layers = info.findall("languages/text-layer", namespaces=nsmap)
            for layer in text_layers:
                lang = langcodes.standardize_tag(layer.attrib["lang"])
                show = bool(distutils.util.strtobool(layer.attrib["show"]))
                self.languages.append(meta.LanguageLayer(lang, show))

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
            ser = meta.Series(se.text)
            if "volume" in se.keys():
                ser.volume = se.attrib["volume"]
            self.series[se.attrib["title"]] = ser

        # Content Rating
        for rt in info.findall("content-rating", namespaces=nsmap):
            type = '_'
            if "type" in rt.keys():
                type = rt.attrib["type"]
            self.content_rating[type] = rt.text

        # Database Reference
        for db in info.findall("databaseref", namespaces=nsmap):
            dbref = meta.DBRef(db.attrib["dbname"], db.text)
            if "type" in db.keys():
                dbref.type = db.attrib["type"]
            self.database_ref.append(dbref)

        #endregion

    @helpers.check_book
    def add_author(self, *names: str, first_name=None, last_name=None, nickname=None) -> meta.Author:
        """Add an Author to the book info. Usage is the same as :class:`Author <libacbf.metadata.Author>`.

        Returns
        -------
        Author
        """
        author = meta.Author(*names, first_name, last_name, nickname)
        self.authors.append(author)
        return author

    @helpers.check_book
    def add_genre(self, genre: str, match: Optional[int] = None):
        """Edit a genre. Add it if it doesn't exist.

        Parameters
        ----------
        genre : str
            See :class:`constants.Genres <libacbf.constants.Genres>` enum for a list of possible values.

        match : int | None, optional
            Set the match percentage of the genre. If ``None``, removes the match value.
        """
        if match < 0 or match > 100:
            raise ValueError("`match` must be an integer from 0 to 100.")
        self.genres[consts.Genres[genre]] = match

    @helpers.check_book
    def add_language(self, lang: str, show: bool):
        """Add a language layer to the book. Usage is the same as
        :class:`LanguageLayer <libacbf.metadata.LanguageLayer>`.
        """
        self.languages.append(meta.LanguageLayer(lang, show))

    @helpers.check_book
    def add_series(self, title: str, sequence: str, volume: Optional[str] = None):
        """Add a series that the book belongs to. ``title`` is the key and usage for value is the same as
        :class:`Series <libacbf.metadata.Series>`.
        """
        self.languages[title] = meta.Series(sequence, volume)

    @helpers.check_book
    def add_dbref(self, dbname: str, ref: str, type: Optional[str] = None):
        """Add a database reference to the book. Usage is the same as :class:`DBRef <libacbf.metadata.DBRef>`.
        """
        self.languages.append(meta.DBRef(dbname, ref, type))


class PublishInfo:
    """Metadata about the book's publisher.

    See Also
    --------
    `Publish-Info section <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Publish-Info_Section>`_.

    Attributes
    ----------
    book : ACBFBook
        Book that the metadata belongs to.

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
    book : ACBFBook
        Book that the metadata belongs to.

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

        self.authors: List[meta.Author] = []
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
    def add_author(self, *names: str, first_name=None, last_name=None, nickname=None) -> meta.Author:
        """Add an Author to the document info. Usage is the same as :class:`Author <libacbf.metadata.Author>`.

        Returns
        -------
        Author
        """
        author = meta.Author(*names, first_name, last_name, nickname)
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
    book : ACBFBook
        Book that this body section belongs to.

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

        self.pages: List[body.Page] = []

        # --- Optional ---
        self.bgcolor: Optional[str] = None

        #region Fill values

        # Background Colour
        if "bgcolor" in body.keys():
            self.bgcolor = body.attrib["bgcolor"]

        # Pages
        for pg in body.findall("page", namespaces=nsmap):
            img_ref = pg.find("image", namespaces=nsmap).attrib["href"]
            page = body.Page(img_ref, book)

            if "bgcolor" in pg.keys():
                page.bgcolor = pg.attrib["bgcolor"]

            if "transition" in pg.keys():
                page.transition = consts.PageTransitions[pg.attrib["transition"]]

            for title in pg.findall("title", namespaces=nsmap):
                lang = '_'
                if "lang" in title.keys():
                    lang = langcodes.standardize_tag(title.attrib["lang"])
                page.title[lang] = title.text

            _fill_page(pg, page, nsmap)

            self.pages.append(page)

        #endregion

    @helpers.check_book
    def insert_page(self, index: int, image_ref: str) -> body.Page:
        """

        Parameters
        ----------
        index : int

        image_ref : str

        Returns
        -------
        Page
        """
        self.pages.insert(index, body.Page(image_ref, self._book))
        return self.pages[index]

    @helpers.check_book
    def append_page(self, image_ref: str) -> body.Page:
        """

        Parameters
        ----------
        image_ref : str

        Returns
        -------
        Page
        """
        page = body.Page(image_ref, self._book)
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
    def add_data(self, target: Union[str, Path], name: str = None, embed: bool = False):
        """Add or embed file at target path into the book.

        Parameters
        ----------
        target : str | Path
            Path to file to be added. Cannot directly write data, target must be a path.

        name : str, optional
            Name to assign to file after writing. Defaults to name part of target.

        embed : bool, default=False
            Whether to embed the file in the ACBF XML. Cannot be ``False`` if book is not an archive type.
        """
        if self._book.archive is None and not embed:
            raise AttributeError("Book is not an archive type. Write data with `embed = True`.")

        if isinstance(target, str):
            target = Path(target).resolve(True)

        name = target.name if name is None else name

        if embed:
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
            raise AttributeError("Book is not an archive type. Write data with `embed = True`.")

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
    str
        Stylesheet as a string.

    Examples
    --------
    To get stylesheets ::

        from libacbf import ACBFBook

        with ACBFBook("path/to/book.cbz") as book:
            style1 = book.styles["style1.css"]  # Style referenced at the top of the ACBF XML as a string.
            embedded_style = book.styles['_']  # Returns the stylesheet embedded in ACBF XML style tag as a string.

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
    def edit_style(self, stylesheet_ref: Union[str, Path], style_name: str = None, type: str = "text/css"):
        """Writes or overwrites file in archive with referenced stylesheet.

        Parameters
        ----------
        stylesheet_ref : str | Path
            Path to stylesheet. Cannot directly write data.

        style_name : str, optional
            Name of stylesheet after being written. Defaults to name part of ``stylesheet_ref``. If it is ``'_'``,
            writes stylesheet to style tag of ACBF XML.

        type : str, default="text/css"
            Mime Type of stylesheet. Defaults to CSS but can be others (like SASS).
        """
        if isinstance(stylesheet_ref, str):
            stylesheet_ref = Path(stylesheet_ref)

        if style_name is None:
            style_name = stylesheet_ref.name

        if style_name == '_':
            with open(stylesheet_ref, "rb") as css:
                self._styles['_'] = css.read()
            self.types['_'] = type
        else:
            if self._book.archive is not None:
                self._book.archive.write(stylesheet_ref, style_name)
            self._styles[style_name] = None
            self.types[style_name] = type

    @helpers.check_book
    def remove_style(self, style_name: str):
        """Remove stylesheet from book.

        Parameters
        ----------
        style_name : str
            Stylesheet to remove. If it is ``'_'``, remove embedded stylesheet.
        """
        self._styles.pop(style_name)
        if self._book.archive is not None:
            self._book.archive.delete(style_name)

    def __len__(self):
        len(self._styles.keys())

    def __getitem__(self, key: str):
        if key not in self.list_styles():
            raise FileNotFoundError(f"`{key}` style could not be found.")

        if self._styles[key] is None:
            if self._book.archive is not None:
                self._styles[key] = self._book.archive.read(key)
            else:
                st_path = self._book.book_path.parent / Path(key)
                with open(str(st_path), "rb") as st:
                    self._styles[key] = st.read()

        return self._styles[key]
