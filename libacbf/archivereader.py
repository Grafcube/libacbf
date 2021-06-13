import os
import shutil
from pathlib import Path
from typing import Optional, Union
from zipfile import ZipFile, is_zipfile
from py7zr import SevenZipFile, is_7zfile
import tarfile as Tar
from rarfile import RarFile, is_rarfile

from libacbf.constants import ArchiveTypes

def get_archive_type(file: Union[str, Path]) -> ArchiveTypes:
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
	if is_zipfile(file):
		return ArchiveTypes.Zip
	elif is_7zfile(file):
		return ArchiveTypes.SevenZip
	elif Tar.is_tarfile(file):
		return ArchiveTypes.Tar
	elif is_rarfile(file):
		return ArchiveTypes.Rar
	else:
		raise ValueError("File is not a supported archive type.")

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
	def __init__(self, archive: Union[str, Path]):
		self.type: ArchiveTypes = get_archive_type(archive)

		if isinstance(archive, str):
			archive = Path(archive)

		arc = None
		if self.type == ArchiveTypes.Zip:
			arc = ZipFile(str(archive), 'r')
		if self.type == ArchiveTypes.SevenZip:
			self.tempdir = Path(archive.parent/('.' + archive.stem.replace(' ', '_') + "-" + ''.join(archive.suffixes)))
			os.makedirs(str(self.tempdir), exist_ok=True)
			arc = SevenZipFile(str(archive), 'r')
		if self.type == ArchiveTypes.Tar:
			arc = Tar.open(str(archive), 'r')
		if self.type == ArchiveTypes.Rar:
			arc = RarFile(str(archive), errors="strict")

		self.archive: Union[ZipFile, SevenZipFile, Path, Tar.TarFile, RarFile] = arc

	def read(self, file_path: Union[str, Path]) -> bytes:
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
		if isinstance(file_path, str):
			file_path = Path(file_path)

		contents = None
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
			with self.archive.open(str(file_path), 'r') as file:
				contents = file.read()

		elif self.type == ArchiveTypes.SevenZip:
			self.archive.reset()
			if not os.path.exists(str(self.tempdir/file_path)):
				self.archive.extract(str(self.tempdir), [str(file_path)])
			with open(str(self.tempdir/file_path), 'rb') as file:
				contents = file.read()

		elif self.type == ArchiveTypes.Tar:
			contents = self.archive.extractfile(str(file_path)).read()

		return contents

	def close(self):
		"""Close archive file object or remove temporary directory.
		"""
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Tar, ArchiveTypes.Rar]:
			self.archive.close()
		elif self.type == ArchiveTypes.SevenZip:
			shutil.rmtree(self.tempdir)

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

		contents = str(self.read(acbf_file), "utf-8")
		return contents

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, traceback):
		self.close()
