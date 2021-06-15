from pathlib import PurePath
from typing import Optional, Union, BinaryIO
import magic
from zipfile import ZipFile, is_zipfile
from py7zr import SevenZipFile, is_7zfile
import tarfile as Tar
from rarfile import RarFile, is_rarfile

from libacbf.constants import ArchiveTypes
from libacbf.exceptions import FailedToReadArchive, InvalidBook, UnsupportedArchive

def get_archive_type(file: Union[str, PurePath, BinaryIO]) -> ArchiveTypes:
	"""[summary]

	Parameters
	----------
	file : Union[str, PurePath]
		[description]

	Returns
	-------
	ArchiveTypes
		[description]

	Raises
	------
	ValueError
		[description]
	"""
	is_path = False
	if not isinstance(file, (str, PurePath)):
		file.seek(0)
		mime_type = magic.from_buffer(file.read(2048), True)
		file.seek(0)
	else:
		is_path = True
		mime_type = magic.from_file(str(file), True)

	is_text = mime_type.startswith("text/")

	if not is_text:
		if is_7zfile(file):
			return ArchiveTypes.SevenZip
		elif is_zipfile(file):
			return ArchiveTypes.Zip

		if is_path:
			if Tar.is_tarfile(file):
				return ArchiveTypes.Tar
			elif is_rarfile(file):
				return ArchiveTypes.Rar
			else:
				raise UnsupportedArchive
		else:
			raise FailedToReadArchive("Tar and RAR archives can only be read from file paths.")
	else:
		raise UnsupportedArchive("File is not an archive file.")

class ArchiveReader:
	"""Class to directly read from archives.

	This class can read Zip, 7Zip, Tar and Rar archives. There shouldn't usually be a reason to use
	this class.

	Attributes
	----------
	archive : zipfile.ZipFile | rarfile.TarFile | rarfile.RarFile | pathlib.PurePath
		If it is a ``Path``, the path is to a temporary directory where a ``py7zr.SevenZipFile`` is
		extracted.

	type : ArchiveTypes(Enum)
		The type of archive.
	"""
	def __init__(self, archive: Union[str, PurePath, BinaryIO]):
		self.type: ArchiveTypes = get_archive_type(archive)

		arc = None
		if self.type == ArchiveTypes.Zip:
			arc = ZipFile(archive, 'r')
		if self.type == ArchiveTypes.SevenZip:
			arc = SevenZipFile(archive, 'r')
		if self.type == ArchiveTypes.Tar:
			arc = Tar.open(archive, 'r')
		if self.type == ArchiveTypes.Rar:
			arc = RarFile(archive)

		self.archive: Union[ZipFile, SevenZipFile, Tar.TarFile, RarFile] = arc

	def read(self, target: str) -> bytes:
		"""Get file as bytes from archive.

		Parameters
		----------
		file_path : str
			Path relative to root of archive.

		Returns
		-------
		bytes
			Contents of file.
		"""
		contents = None

		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
			with self.archive.open(target, 'r') as file:
				contents = file.read()

		elif self.type == ArchiveTypes.SevenZip:
			self.archive.reset()
			with self.archive.read([target])[target] as file:
				contents = file.read()

		elif self.type == ArchiveTypes.Tar:
			with self.archive.extractfile(target) as file:
				contents = file.read()

		return contents

	def close(self):
		"""Close archive file object or remove temporary directory.
		"""
		self.archive.close()

	def _get_acbf_contents(self) -> Optional[str]:
		acbf_file = None
		contents = None
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
			for i in self.archive.infolist():
				if not i.is_dir() and '/' not in i.filename and i.filename.endswith(".acbf"):
					acbf_file = i.filename
					break
		elif self.type == ArchiveTypes.SevenZip:
			for i in self.archive.list():
				if not i.is_directory and '/' not in i.filename and i.filename.endswith(".acbf"):
					acbf_file = i.filename
					break
		elif self.type == ArchiveTypes.Tar:
			for i in self.archive.getmembers():
				if i.isfile() and '/' not in i.name and i.name.endswith(".acbf"):
					acbf_file = i.name
					break

		if acbf_file is None:
			raise InvalidBook

		contents = str(self.read(acbf_file), "utf-8")
		return contents

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, traceback):
		self.close()
