class UnsupportedArchive(Exception):
	def __init__(self, message: str ="File is not a supported archive type.", *args, **kwargs):
		super().__init__(message, *args, **kwargs)

class FailedToReadArchive(Exception):
	def __init__(self, message: str, *args, **kwargs):
		super().__init__(message, *args, **kwargs)

class InvalidBook(Exception):
	def __init__(self, message: str ="File is not an ACBF Ebook.", *args, **kwargs):
		super().__init__(message, *args, **kwargs)

class EditRARArchiveError(Exception):
	def __init__(self, message: str ="Editing RAR Archives is not supported.", *args, **kwargs):
		super().__init__(message, *args, **kwargs)
