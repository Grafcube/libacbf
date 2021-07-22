class UnsupportedArchive(Exception):
    def __init__(self, message: str = "File is not a supported archive type.", *args):
        super().__init__(message, *args)


class InvalidBook(Exception):
    def __init__(self, message: str = "File is not an ACBF Ebook.", *args):
        super().__init__(message, *args)


class EditRARArchiveError(Exception):
    def __init__(self, message: str = "Editing RAR Archives is not supported.", *args):
        super().__init__(message, *args)
