from io import UnsupportedOperation
from pathlib import Path
from typing import Optional, Union, Literal, BinaryIO
from tempfile import TemporaryDirectory
from zipfile import ZipFile, is_zipfile
from py7zr import SevenZipFile, is_7zfile
import tarfile as tar
from rarfile import RarFile, is_rarfile

from libacbf.constants import ArchiveTypes
from libacbf.exceptions import EditRARArchiveError, InvalidBook, UnsupportedArchive

def get_archive_type(file: Union[str, Path, BinaryIO]) -> ArchiveTypes:
	"""[summary]

	Parameters
	----------
	file : Union[str, Path]
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
	if is_7zfile(file):
		return ArchiveTypes.SevenZip
	elif is_zipfile(file):
		return ArchiveTypes.Zip
	elif is_rarfile(file):
		return ArchiveTypes.Rar
	elif tar.is_tarfile(file):
		return ArchiveTypes.Tar
	else:
		raise UnsupportedArchive

class ArchiveReader:
	"""Class to directly read from archives.

	This class can read Zip, 7Zip, Tar and Rar archives. There shouldn't usually be a reason to use
	this class.

	Attributes
	----------
	archive : zipfile.ZipFile | rarfile.TarFile | rarfile.RarFile | pathlib.Path
		If it is a ``Path``, the path is to a temporary directory where a ``py7zr.SevenZipFile`` is
		extracted.

	type : ArchiveTypes(Enum)
		The type of archive.
	"""
	def __init__(self, archive: Union[str, Path, BinaryIO], mode: Literal['r', 'a'] = 'r'):
		if isinstance(archive, str):
			archive = Path(archive).resolve(True)

		if not isinstance(archive, Path):
			archive.seek(0)

		self.mode: Literal['r', 'a'] = mode
		self.type: ArchiveTypes = get_archive_type(archive)

		if mode != 'r' and self.type == ArchiveTypes.Rar:
			raise EditRARArchiveError

		arc = None
		if self.type == ArchiveTypes.Zip:
			arc = ZipFile(archive, mode)
		elif self.type == ArchiveTypes.SevenZip:
			arc = SevenZipFile(archive, mode)
		elif self.type == ArchiveTypes.Tar:
			if isinstance(archive, (str, Path)):
				arc = tar.open(archive, mode=mode)
			else:
				arc = tar.open(fileobj=archive, mode=mode)
		elif self.type == ArchiveTypes.Rar:
			arc = RarFile(archive)

		self.archive: Union[ZipFile, SevenZipFile, tar.TarFile, RarFile] = arc

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

	def write(self, file: Union[str, Path], arcname: Optional[str] = None):
		"""[summary]

		Parameters
		----------
		file : str | Path
			[description]
		arcname : str | None, default=None
			[description]
		"""
		if self.mode == 'r':
			UnsupportedOperation("File is not writeable.")

		if isinstance(file, str):
			file = Path(file)
			if arcname is None:
				arcname = file.name
		file = str(file.resolve(True))

		if self.type in [ArchiveTypes.Zip, ArchiveTypes.SevenZip]:
			self.archive.write(file, arcname)
		elif self.type == ArchiveTypes.Tar:
			with TemporaryDirectory() as target:
				pass
			raise NotImplementedError("Fully extract and recompress on save?")

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
