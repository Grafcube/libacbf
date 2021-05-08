from io import BytesIO
import shutil
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Union
from tempfile import mkdtemp
from zipfile import ZipFile
from py7zr import SevenZipFile
import tarfile as Tar
from rarfile import RarFile

class ArchiveReader:
	"""
	docstring
	"""
	def __init__(self, archive_path: Union[str, Path]):
		if type(archive_path) is str:
			archive_path = Path(archive_path)

		archive = None
		if archive_path.suffix in [".cbz", ".zip"]:
			ar = ArchiveTypes.Zip
			archive = ZipFile(str(archive_path), 'r')

		elif archive_path.suffix in [".cb7", ".7z"]:
			ar = ArchiveTypes.SevenZip
			archive = Path(mkdtemp())
			with SevenZipFile(str(archive_path), 'r') as sarchive:
				sarchive.extractall(str(archive))

		elif "".join(archive_path.suffixes) in [".cbt", ".tar", ".tar.gz"]:
			ar = ArchiveTypes.Tar

		elif archive_path.suffix in [".cbr", ".rar"]:
			ar = ArchiveTypes.Rar

		self.archive: Union[ZipFile, Path, Tar.TarFile, RarFile] = archive

		self.type: ArchiveTypes = ar

	def get_acbf_contents(self) -> Optional[str]:
		contents = None
		if self.type == ArchiveTypes.Zip:
			for i in self.archive.namelist():
				i = str(i)
				if "/" not in i and i.endswith(".acbf"):
					with self.archive.open(i, 'r') as book:
						contents = str(book.read(), "utf-8")
					break
		elif self.type == ArchiveTypes.SevenZip:
			acbf_files = list(self.archive.glob("*.acbf"))
			if len(acbf_files) > 0:
				with open(acbf_files[0], 'r', encoding="utf-8") as book:
					contents = book.read()
		elif self.type == ArchiveTypes.Tar:
			pass
		elif self.type == ArchiveTypes.Rar:
			pass
		return contents

	def read(self, file_path: str) -> bytes:
		contents = None
		if self.type == ArchiveTypes.Zip:
			with self.archive.open(file_path, 'r') as file:
				contents = file.read()
		elif self.type == ArchiveTypes.SevenZip:
			with open(str(self.archive/Path(file_path)), 'rb') as file:
				contents = file.read()
		elif self.type == ArchiveTypes.Tar:
			pass
		elif self.type == ArchiveTypes.Rar:
			pass
		return contents

	def close(self):
		if self.type == ArchiveTypes.Zip:
			self.archive.close()
		elif self.type == ArchiveTypes.SevenZip:
			shutil.rmtree(str(self.archive))
		elif self.type == ArchiveTypes.Tar:
			pass
		elif self.type == ArchiveTypes.Rar:
			pass

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, traceback):
		self.close()

class ArchiveTypes(Enum):
	Zip = 0
	SevenZip = auto()
	Tar = auto()
	Rar = auto()
