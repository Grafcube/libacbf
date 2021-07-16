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

def get_book_template() -> str:
    """[summary]

    Returns
    -------
    str
        [description]
    """
    with open("libacbf/templates/base_template_1.1.acbf", 'r') as template:
        contents = template.read()
    return contents

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
            warnings.warn("Validation failed. Books with 1.0 schema are not fully supported.",
                          UserWarning)
            warnings.warn('Change the ACBF tag at the top of the `.acbf` XML file to \
                         `<ACBF xmlns="http://www.acbf.info/xml/acbf/1.1">` to use the 1.1 schema.',
                          UserWarning)
            print(err)
    else:
        acbf_schema.assertValid(tree)

class ACBFBook:
    """Base class for reading ACBF ebooks.

    Parameters
    ----------
    file : str, default=Empty book template
        Path to ACBF book. May be absolute or relative.

    Raises
    ------
    ValueError (File is not an ACBF Ebook.)
        Raised if the XML does not match ACBF schema or if archive does not contain ACBF file.

    See Also
    --------
    `ACBF Specifications <https://acbf.fandom.com/wiki/Advanced_Comic_Book_Format_Wiki>`_.

    Examples
    --------
    A book object can be opened, read and then closed. It can read files with the extensions
    ``.acbf``, ``.cbz``, ``.cb7``, ``.cbt``, ``.cbr``. ::

        from libacbf import ACBFBook

        book = ACBFBook("path/to/file.cbz")
        # Read data from book
        book.close()

    ``ACBFBook`` is also a context manager and can be used in with statements. ::

        from libacbf import ACBFBook

        with ACBFBook("path/to/file.cbz") as book:
            # Read data from book

    Attributes
    ----------
    Metadata : ACBFMetadata
        See :class:`ACBFMetadata <libacbf.libacbf.ACBFMetadata>` for more information.

    Body : ACBFBody
        See :class:`ACBFBody <libacbf.libacbf.ACBFBody>` for more information.

    Data : ACBFData
        See :class:`ACBFData <libacbf.libacbf.ACBFData>` for more information.

    References : dict
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

    Styles : dict-like object
        Get styles linked in the ACBF file.

        An object that behaves like a dictionary. Use ``Styles[file name]`` to get the contents of
        the stylesheet as a string. Use ``list_styles()`` to get list of all available styles. All
        paths are relative. ::

            style = book.Styles["style_name.css"]

        If a style is embedded in the ACBF file, use ``Styles['_']`` to get its contents. ::

            embedded_stylesheet = book.Styles['_']

    book_path : Path
        Absolute path to source file.

    archive : ArchiveReader, optional
        Can be used to read archive directly if file is not ``.acbf``. There probably wont be any
        reason to use this.

        :attr:`ArchiveReader.archive <libacbf.archivereader.ArchiveReader.archive>` may be
        ``zipfile.ZipFile``, ``py7zr.SevenZipFile``, ``tarfile.TarFile`` or ``rarfile.RarFile``.
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

                nonlocal arc_mode
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
            arc_mode = 'w'
            if mode == 'a':
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

        self.Styles: Styles = Styles(self, str(contents))

        self.Metadata: ACBFMetadata = ACBFMetadata(self)

        self.Body: ACBFBody = ACBFBody(self)

        self.Data: ACBFData = ACBFData(self)

        self.References: Dict[str, Dict[str, str]] = {}
        self.sync_references()

    def get_acbf_xml(self) -> str:
        """[summary]

        Returns
        -------
        [type]
            [description]
        """
        return etree.tostring(self._root.getroottree(), encoding="utf-8", xml_declaration=True,
                              pretty_print=True).decode("utf-8")

    def save(self, file: Union[str, Path, IO, None] = None, overwrite: bool = False):
        """Save as file.

        Parameters
        ----------
        file : str, optional
            Path to save to.
        overwrite : bool, optional
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
        """
        Saves the book and closes open archives if file is ``.cbz``, ``.cbt`` or ``.cbr``
        or ``.cb7`` files.
        """
        if self.mode == 'x':
            self.save()
        elif self.mode in ['w', 'a']:
            self.save(overwrite=True)

        self.mode = 'r'
        self.is_open = False

        if self.archive is not None:
            self.archive.close()

    def sync_references(self):
        ns = self._namespace
        ref_root = self._root.find(f"{ns}references")
        self.References.clear()
        if ref_root is not None:
            reference_items = ref_root.findall(f"{ns}reference")
            for ref in reference_items:
                pa = []
                for p in ref.findall(f"{ns}p"):
                    text = re.sub(r'</?p[^>]*>', '',
                                  etree.tostring(p, encoding="utf-8").decode("utf-8").strip())
                    pa.append(text)
                self.References[ref.attrib["id"]] = {"paragraph": '\n'.join(pa)}

    def edit_reference(self, id: str, text: str):
        """[summary]

        Parameters
        ----------
        id : str
            [description]
        text : str
            [description]
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

        if id not in self.References:
            self.References[id] = {"paragraph": ''}
        self.References[id]["paragraph"] = text

    def remove_reference(self, id: str):
        """[summary]

        Parameters
        ----------
        id : str
            [description]
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

            self.References.pop(id)

    def __repr__(self):
        if self.is_open:
            return object.__repr__(self).replace("libacbf.libacbf.ACBFBook", "libacbf.ACBFBook")
        else:
            return "<libacbf.ACBFBook [Closed]>"

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

class ACBFMetadata:
    """Class to read metadata of the book.

    See Also
    --------
    `Meta-data Section Definition <https://acbf.fandom.com/wiki/Meta-data_Section_Definition>`_.

    Attributes
    ----------
    book : ACBFBook
        Book that this metadata belongs to.

    book_info : BookInfo
        See :class:`BookInfo <libacbf.metadata.BookInfo>`.

    publisher_info : PublishInfo
        See :class:`PublishInfo <libacbf.metadata.PublishInfo>`.

    document_info : DocumentInfo
        See :class:`DocumentInfo <libacbf.metadata.DocumentInfo>`.
    """

    def __init__(self, book: ACBFBook):
        self.book = book
        ns = book._namespace
        meta_root = book._root.find(f"{ns}meta-data")

        self.book_info: BookInfo = BookInfo(meta_root.find(f"{ns}book-info"), book)
        self.publisher_info: PublishInfo = PublishInfo(meta_root.find(f"{ns}publish-info"), book)
        self.document_info: DocumentInfo = DocumentInfo(meta_root.find(f"{ns}document-info"), book)

class ACBFBody:
    """Body section contains the definition of individual book pages, text layers, frames and jumps
    inside those pages.

    See Also
    --------
    `Body Section Definition <https://acbf.fandom.com/wiki/Body_Section_Definition>`_.

    Attributes
    ----------
    book : ACBFBook
        Book that this body section belongs to.

    pages : List[Page]
        A list of :class:`Page <libacbf.body.Page>` objects in order.

    bgcolor : str, optional
        Defines a background colour for the whole book. Can be overridden by ``bgcolor`` in pages,
        text layers and text areas.
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
    def insert_new_page(self, index: int, image_ref: str) -> Page:
        pg = etree.Element(f"{self._ns}page")
        self._body.insert(index, pg)
        etree.SubElement(pg, f"{self._ns}image", {"href": image_ref})
        self.pages.insert(index, Page(pg, self.book))
        return self.pages[index]

    @helpers.check_book
    def remove_page(self, index: int):
        pg = self.pages.pop(index)
        pg._page.clear()
        self._body.remove(pg._page)

    @helpers.check_book
    def change_page_index(self, src_index: int, dest_index: int):
        pg = self.pages.pop(src_index)
        self._body.remove(pg._page)
        self._body.insert(dest_index, pg._page)
        self.pages.insert(dest_index, pg)

    # --- Optional ---
    @helpers.check_book
    def set_bgcolor(self, bg: Optional[str]):
        if bg is not None:
            self._body.set("bgcolor", bg)
        elif "bgcolor" in self._body.attrib:
            self._body.attrib.pop("bgcolor")
        self.bgcolor = bg

class ACBFData:
    """Get any binary data embedded in the ACBF file.

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
            image = book.Data["image.png"]
            font = book.Data["font.ttf"]
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
        if self.book.archive is None and not embed:
            raise AttributeError("Book is not an archive type. Write data with `embed = True`.")

        if isinstance(target, str) and not embed:
            target = Path(target)

        if embed:
            data_elements = self.book._root.findall(f"{self._ns}data/{self._ns}binary")
            for i in data_elements:
                if i.attrib["id"] == target:
                    i.clear()
                    i.getparent().remove(i)
            self.files.pop(target)
        else:
            self.book.archive.remove(target)

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
    def __init__(self, book: ACBFBook, contents: str):
        self.book = book
        self._contents = contents

        self.styles: Dict[str, Optional[str]] = {}
        self.sync_styles()

    def list_styles(self) -> List[str]:
        return [str(x) for x in self.styles.keys()]

    def sync_styles(self):
        self.styles.clear()
        style_refs = [x for x in self.book._root.xpath("//processing-instruction()") if
                      x.target == "xml-stylesheet"]
        for i in style_refs:
            self.styles[i.attrib["href"]] = None
        if self.book._root.find(f"{self.book._namespace}style") is not None:
            self.styles['_'] = None

    @helpers.check_book
    def edit_style(self, stylesheet_ref: Union[str, Path], style_name: Optional[str] = None,
                   type: str = "text/css", embed: bool = False):

        if isinstance(stylesheet_ref, str):
            stylesheet_ref = Path(stylesheet_ref)

        if style_name is None and not embed:
            style_name = stylesheet_ref.name

        if embed:
            style_element = self.book._root.find(f"{self.book._namespace}style")
            if style_element is None:
                style_element = etree.SubElement(self.book._root, f"{self.book._namespace}style",
                                                 {"type": type})
            with open(stylesheet_ref, 'r') as css:
                style_element.text = css.read().strip()
            self.styles['_'] = style_element.text
        else:
            style_refs = [x.attrib["href"] for x in
                          self.book._root.xpath("//processing-instruction()") if
                          x.target == "xml-stylesheet"]
            if style_name not in style_refs:
                style_element = etree.ProcessingInstruction("xml-stylesheet",
                                                            f'type="{type}" href="{style_name}"')
                self.book._root.addprevious(style_element)
            if self.book.archive is not None:
                self.book.archive.write(stylesheet_ref, style_name)

    @helpers.check_book
    def remove_style(self, style_name: str):
        style_refs = [x for x in self.book._root.xpath("//processing-instruction()") if
                      x.target == "xml-stylesheet"]
        for i in style_refs:
            if i.target == "xml-stylesheet" and i.attrib["href"] == style_name:
                self.book._root.append(i)
                self.book._root.remove(i)
                break
        if self.book.archive is not None:
            self.book.archive.remove(style_name)

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
