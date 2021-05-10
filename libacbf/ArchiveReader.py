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

		elif archive_path.suffix in [".cbt", ".tar", ".gz"]:
			ar = ArchiveTypes.Tar
			archive = Tar.open(str(archive_path), 'r')

		elif archive_path.suffix in [".cbr", ".rar"]:
			ar = ArchiveTypes.Rar
			raise NotImplementedError
			# archive = RarFile(str(archive_path), 'r')

		self.archive: Union[ZipFile, Path, Tar.TarFile, RarFile] = archive

		self.type: ArchiveTypes = ar

	def get_acbf_contents(self) -> Optional[str]:
		contents = None
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
			for i in self.archive.infolist():
				if not i.is_dir() and '/' not in i.filename and i.filename.endswith(".acbf"):
					with self.archive.open(i, 'r') as book:
						contents = str(book.read(), "utf-8")
					break
		elif self.type == ArchiveTypes.SevenZip:
			acbf_files = list(self.archive.glob("*.acbf"))
			if len(acbf_files) > 0:
				with open(acbf_files[0], 'r', encoding="utf-8") as book:
					contents = book.read()
		elif self.type == ArchiveTypes.Tar:
			for i in self.archive.getmembers():
				if i.isfile() and '/' not in i.name and i.name.endswith(".acbf"):
					contents = str(self.archive.extractfile(i).read(), encoding="utf-8")
					break
		return contents

	def read(self, file_path: str) -> bytes:
		contents = None
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
			with self.archive.open(file_path, 'r') as file:
				contents = file.read()
		elif self.type == ArchiveTypes.SevenZip:
			with open(str(self.archive/Path(file_path)), 'rb') as file:
				contents = file.read()
		elif self.type == ArchiveTypes.Tar:
			contents = self.archive.extractfile(file_path).read()
		return contents

	def close(self):
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Tar, ArchiveTypes.Rar]:
			self.archive.close()
		elif self.type == ArchiveTypes.SevenZip:
			shutil.rmtree(str(self.archive))

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, traceback):
		self.close()

class ArchiveTypes(Enum):
	Zip = 0
	SevenZip = auto()
	Tar = auto()
	Rar = auto()
