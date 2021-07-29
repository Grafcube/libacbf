import os
import re
import warnings
import tempfile
import magic
from io import TextIOBase, UnsupportedOperation
from pathlib import Path
from typing import List, Dict, Optional, Set, Union, Literal, IO
from base64 import b64encode
from lxml import etree
from zipfile import ZipFile
from py7zr import SevenZipFile
import tarfile as tar

import libacbf.helpers as helpers
from libacbf.constants import ArchiveTypes
from libacbf.metadata import BookInfo, PublishInfo, DocumentInfo
from libacbf.body import Page
from libacbf.bookdata import BookData
from libacbf.archivereader import ArchiveReader
from libacbf.exceptions import InvalidBook, EditRARArchiveError


def _validate_acbf(tree, ns: str):
    version = re.split(r'/', re.sub(r'[{}]', '', ns))[-1]
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


def get_book_template() -> str:
    """Get the bare minimum XML required to create an ACBF book.

    Warning
    -------
    Some properties will already exist and have default values. See (INSERT LINK HERE) for more details.

    Returns
    -------
    str
        XML string template.
    """
    with open("libacbf/templates/base_template_1.1.acbf", 'r') as template:
        contents = template.read()
    return contents


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

        Warning
        -------
        You can only write data by embedding when this is ``None``.

    Raises
    ------
    EditRARArchiveError
        Raised if ``mode`` parameter is not ``'r'`` but file is a Rar archive.

    InvalidBook
        Raised if the XML does not match ACBF schema or if archive does not contain ACBF file.

    Notes
    -----
    Archive formats use the defaults of each type like compression level etc. Manage the archives yourself if you want
    to change this. Image refs that are relative paths check within the archive if the book is an archive. Otherwise it
    checks relative to the '.acbf' file. So you can simply use a directory to manage the book and archive it with your
    own settings when you are done.

    See Also
    --------
    `ACBF Specifications <https://acbf.fandom.com/wiki/Advanced_Comic_Book_Format_Wiki>`_.

    Warning
    -------
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
        See :class:`ACBFBody` for more information.

    data : ACBFData
        See :class:`ACBFData` for more information.

    references : dict
        A dictionary that contains a list of particular references that occur inside the
        main document body. Keys are unique reference ids and values are dictionaries that contain
        a ``paragraph`` key with text. ::

            {
                "ref_id_001": {
                    "paragraph": "This is a reference."
                }
                "ref_id_002": {
                    "paragraph": "This is another reference."
                }
            }

        ``paragraph`` can contain special tags for formatting. For more information and a full list,
        see :attr:`TextArea.paragraph <libacbf.body.TextArea.paragraph>`.

    styles : Styles
        See :class:`Styles` for more information.

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
        self.book_path: Path = None

        self.archive: Optional[ArchiveReader] = None

        self.mode: Literal['r', 'w', 'a', 'x'] = mode

        self.is_open: bool = True

        self._source = file

        if isinstance(file, str):
            self.book_path = Path(file).resolve()
        if isinstance(file, Path):
            self.book_path = file.resolve()

        archive_type = ArchiveTypes[archive_type] if archive_type is not None else None
        is_text = archive_type is None
        if isinstance(file, TextIOBase):
            archive_type = None
            is_text = True

        if archive_type == ArchiveTypes.Rar and mode != 'r':
            raise EditRARArchiveError

        arc_mode = mode

        def create_file():
            if not is_text:
                arc = None
                if archive_type == ArchiveTypes.Zip:
                    arc = ZipFile(file, 'w')
                elif archive_type == ArchiveTypes.SevenZip:
                    arc = SevenZipFile(file, 'w')
                elif archive_type == ArchiveTypes.Tar:
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

        if mode in ['r', 'a']:
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

        self._namespace: str = r"{" + self._root.nsmap[None] + r"}"

        _validate_acbf(self._root.getroottree(), self._namespace)

        self.styles: Styles = Styles(self, str(contents))

        self.book_info: BookInfo = BookInfo(
            self._root.find(f"{self._namespace}meta-data/{self._namespace}book-info"), self)

        self.publisher_info: PublishInfo = PublishInfo(
            self._root.find(f"{self._namespace}meta-data/{self._namespace}publish-info"), self)

        self.document_info: DocumentInfo = DocumentInfo(
            self._root.find(f"{self._namespace}meta-data/{self._namespace}document-info"), self)

        self.body: ACBFBody = ACBFBody(self)

        self.data: ACBFData = ACBFData(self)

        self.references: Dict[str, Dict[str, str]] = {}
        self.sync_references()

    def get_acbf_xml(self) -> str:
        """Converts the XML tree to a string.

        Returns
        -------
        str
            ACBF book's XML data.
        """
        return etree.tostring(self._root.getroottree(), encoding="utf-8", xml_declaration=True,
                              pretty_print=True).decode("utf-8")

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

        _validate_acbf(self._root.getroottree(), self._namespace)

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
                    book.write(self.get_acbf_xml())
            else:
                file.write(self.get_acbf_xml())
        else:
            acbf_path = Path(tempfile.gettempdir()) / self.archive._get_acbf_file()
            with open(acbf_path, 'w') as xml:
                xml.write(self.get_acbf_xml())
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

    def sync_references(self):
        ns = self._namespace
        ref_root = self._root.find(f"{ns}references")
        self.references.clear()
        if ref_root is not None:
            reference_items = ref_root.findall(f"{ns}reference")
            for ref in reference_items:
                pa = []
                for p in ref.findall(f"{ns}p"):
                    text = re.sub(r'</?p[^>]*>', '', etree.tostring(p, encoding="utf-8").decode("utf-8").strip())
                    pa.append(text)
                self.references[ref.attrib["id"]] = {"paragraph": '\n'.join(pa)}

    def edit_reference(self, id: str, text: str):
        """Edit the reference by id. Create it if it does not exist.

        Parameters
        ----------
        id : str
            Reference id. It is unique so be careful of overwriting.

        text : str
            Text of reference. Can be multiline. Does not use special formatting.
        """
        helpers.check_write(self)

        ref_section = self._root.find(f"{self._namespace}references")
        if ref_section is None:
            ref_section = etree.Element(f"{self._namespace}references")
            self._root.append(ref_section)

        ref_items = ref_section.findall(f"{self._namespace}reference")

        ref_element = None
        for i in ref_items:
            if i.attrib["id"] == id:
                ref_element = i
                break

        if ref_element is None:
            ref_element = etree.Element(f"{self._namespace}reference")
            ref_section.append(ref_element)

        ref_element.clear()
        ref_element.set("id", id)

        p_list = re.split(r'\n', text)
        for ref in p_list:
            p = f"<p>{ref}</p>"
            p_element = etree.fromstring(bytes(p, encoding="utf-8"))
            for i in list(p_element.iter()):
                i.tag = self._namespace + i.tag
            ref_element.append(p_element)

        if id not in self.references:
            self.references[id] = {"paragraph": ''}
        self.references[id]["paragraph"] = text

    def remove_reference(self, id: str):
        """Remove a reference by unique id.

        Parameters
        ----------
        id : str
            Reference id.
        """
        helpers.check_write(self)

        ref_section = self._root.find(f"{self._namespace}references")

        if ref_section is not None:
            for i in ref_section.findall(f"{self._namespace}reference"):
                if i.attrib["id"] == id:
                    i.clear()
                    ref_section.remove(i)
                    break

            if len(ref_section.findall(f"{self._namespace}reference")) == 0:
                ref_section.getparent().remove(ref_section)

            self.references.pop(id)

    def __repr__(self):
        if self.is_open:
            return object.__repr__(self).replace("libacbf.libacbf.ACBFBook", "libacbf.ACBFBook")
        else:
            return "<libacbf.ACBFBook [Closed]>"

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


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
        self.book = book

        self._ns = book._namespace
        self._body = book._root.find(f"{self._ns}body")

        self.pages: List[Page] = []
        self.sync_pages()

        # Optional
        self.bgcolor: Optional[str] = None
        if "bgcolor" in self._body.keys():
            self.bgcolor = self._body.attrib["bgcolor"]

    def sync_pages(self):
        self.pages.clear()
        for pg in self._body.findall(f"{self._ns}page"):
            self.pages.append(Page(pg, self.book))

    @helpers.check_book
    def insert_new_page(self, index: int, image_ref: str):
        """Insert a new page at an index of the book.

        Parameters
        ----------
        index : int
            Index of the page.

        image_ref : str
            The image that the page shows. See :attr:`Page.image_ref <libacbf.body.Page.image_ref>` for information
            on how to format it.
        """
        pg = etree.Element(f"{self._ns}page")
        self._body.insert(index, pg)
        etree.SubElement(pg, f"{self._ns}image", {"href": image_ref})
        self.pages.insert(index, Page(pg, self.book))

    @helpers.check_book
    def remove_page(self, index: int):
        """Removes the page at index.

        Parameters
        ----------
        index : int
            Index of page to remove.
        """
        pg = self.pages.pop(index)
        pg._page.clear()
        self._body.remove(pg._page)

    @helpers.check_book
    def reorder_page(self, src_index: int, dest_index: int):
        """Move page in book.

        Parameters
        ----------
        src_index : int
            Index of page to move.

        dest_index : int
            Index to move page to.
        """
        pg = self.pages.pop(src_index)
        self._body.remove(pg._page)
        self._body.insert(dest_index, pg._page)
        self.pages.insert(dest_index, pg)

    # --- Optional ---
    @helpers.check_book
    def set_bgcolor(self, bg: Optional[str]):
        """Set background colour of body. Must be a hex colour code starting with ``#``. Value can be removed by passing
        ``None``.

        Parameters
        ----------
        bg : str | None
            Background colour of body.
        """
        if bg is not None:
            self._body.set("bgcolor", bg)
        elif "bgcolor" in self._body.attrib:
            self._body.attrib.pop("bgcolor")
        self.bgcolor = bg


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
        self._ns = book._namespace
        self.book: ACBFBook = book
        self.files: Dict[str, Optional[BookData]] = {}
        self.sync_data()

    def list_files(self) -> Set[str]:
        """Returns a list of all the names of the files embedded in the ACBF file. May be images,
        fonts etc.

        Returns
        -------
        Set[str]
            A set of file names.
        """
        return set(self.files.keys())

    def sync_data(self):
        self.files.clear()
        data_elements = self.book._root.findall(f"{self._ns}data/{self._ns}binary")
        for i in data_elements:
            self.files[i.attrib["id"]] = None

    @helpers.check_book
    def add_data(self, target: Union[str, Path], name: str = '', embed: bool = False):
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
        if self.book.archive is None and not embed:
            raise AttributeError("Book is not an archive type. Write data with `embed = True`.")

        if isinstance(target, str):
            target = Path(target).resolve(True)

        name = target.name if name == '' else name

        if embed:
            base = self.book._root.find(f"{self._ns}data")
            if base is None:
                base = etree.SubElement(self.book._root, f"{self._ns}data")

            bin_element = None
            for i in base.findall(f"{self._ns}binary"):
                if i.attrib["id"] == name:
                    bin_element = i
                    break

            if bin_element is None:
                bin_element = etree.SubElement(base, f"{self._ns}binary", {"id": name})

            with open(target, 'rb') as file:
                contents = file.read()
            type = magic.from_buffer(contents, True)
            data = b64encode(contents).decode("utf-8")

            bin_element.set("content-type", type)
            bin_element.text = data

            self.files[name] = BookData(name, type, data)
        else:
            self.book.archive.write(target, name)

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
        if self.book.archive is None and not embed:
            raise AttributeError("Book is not an archive type. Write data with `embed = True`.")

        if isinstance(target, str) and not embed:
            target = Path(target)

        if embed:
            if not isinstance(target, str):
                target = str(target)
            data_elements = self.book._root.findall(f"{self._ns}data/{self._ns}binary")
            for i in data_elements:
                if i.attrib["id"] == target:
                    i.clear()
                    i.getparent().remove(i)
            self.files.pop(target)
        else:
            if isinstance(target, str):
                target = Path(target)
            self.book.archive.delete(target)

    def __len__(self):
        return len(self.files.keys())

    def __getitem__(self, key: str):
        if key in self.files.keys():
            if self.files[key] is not None:
                return self.files[key]
            else:
                data_elements = self.book._root.findall(f"{self._ns}data/{self._ns}binary")
                for i in data_elements:
                    if i.attrib["id"] == key:
                        new_data = BookData(key, i.attrib["content-type"], i.text)
                        self.files[key] = new_data
                        return new_data
        else:
            raise FileNotFoundError


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
    """

    def __init__(self, book: ACBFBook, contents: str):
        self.book = book
        self._contents = contents

        self.styles: Dict[str, Optional[str]] = {}
        self.sync_styles()

    def list_styles(self) -> Set[str]:
        """All the stylesheets referenced by the ACBF XML.

        Returns
        -------
        Set[str]
            Referenced stylesheets.
        """
        return set(self.styles.keys())

    def sync_styles(self):
        self.styles.clear()
        style_refs = [x for x in self.book._root.xpath("//processing-instruction()") if x.target == "xml-stylesheet"]
        for i in style_refs:
            self.styles[i.attrib["href"]] = None
        if self.book._root.find(f"{self.book._namespace}style") is not None:
            self.styles['_'] = None

    @helpers.check_book
    def edit_style(self, stylesheet_ref: Union[str, Path], style_name: Optional[str] = None, type: str = "text/css"):
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
            style_element = self.book._root.find(f"{self.book._namespace}style")
            if style_element is None:
                style_element = etree.SubElement(self.book._root, f"{self.book._namespace}style", {"type": type})
            with open(stylesheet_ref, 'r') as css:
                style_element.text = css.read().strip()
            self.styles['_'] = style_element.text
        else:
            style_refs = [x.attrib["href"] for x in self.book._root.xpath("//processing-instruction()") if
                          x.target == "xml-stylesheet"]
            if style_name not in style_refs:
                style_element = etree.ProcessingInstruction("xml-stylesheet", f'type="{type}" href="{style_name}"')
                self.book._root.addprevious(style_element)
            if self.book.archive is not None:
                self.book.archive.write(stylesheet_ref, style_name)

    @helpers.check_book
    def remove_style(self, style_name: str):
        """Remove stylesheet from book.

        Parameters
        ----------
        style_name : str
            Stylesheet to remove. If it is ``'_'``, remove embedded stylesheet.
        """
        if style_name == '_':
            st_element = self.book._root.find(f"{self.book._namespace}style")
            if st_element is not None:
                st_element.clear()
                self.book._root.remove(st_element)
                self.styles.pop('_')
        else:
            style_refs = [x for x in self.book._root.xpath("//processing-instruction()") if
                          x.target == "xml-stylesheet"]
            for i in style_refs:
                if i.attrib["href"] == style_name:
                    self.book._root.append(i)
                    self.book._root.remove(i)
                    break
            if self.book.archive is not None:
                self.book.archive.delete(style_name)

    def __len__(self):
        len(self.styles.keys())

    def __getitem__(self, key: str):
        if key in self.styles.keys():
            if self.styles[key] is not None:
                return self.styles[key]
            elif key == '_':
                self.styles['_'] = self.book._root.find(f"{self.book._namespace}style").text.strip()
            else:
                if self.book.archive is None:
                    st_path = self.book.book_path.parent / Path(key)
                    with open(str(st_path), 'r') as st:
                        self.styles[key] = st.read()
                else:
                    self.styles[key] = self.book.archive.read(key).decode("utf-8")
            return self.styles[key]
        else:
            raise FileNotFoundError
