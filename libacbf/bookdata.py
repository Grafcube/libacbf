from typing import Optional, Union
from base64 import b64decode


class BookData:
    """Binary data referenced or stored in the book.

    See Also
    --------
    `Binary data specifications <https://acbf.fandom.com/wiki/Data_Section_Definition#Binary>`_.

    Attributes
    ----------
    id : str
        Name of the file with extension.

    file_type : str
        Mime type of the file.

    data : bytes
        The actual file's data.
    """

    def __init__(self, id: str, file_type: str, data: Union[str, bytes]):
        self._base64data: Optional[str] = None

        self.id: str = id
        self.type: str = file_type

        if isinstance(data, str):
            self._base64data = data
            data = b64decode(self._base64data)

        self.is_embedded: bool = self._base64data is not None
        self.data: bytes = data

    def __repr__(self):
        return f'<libacbf.bookdata.BookData id="{self.id}" type"{self.type}" is_embedded="{self.is_embedded}">'
