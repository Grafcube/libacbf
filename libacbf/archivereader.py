import os
import shutil
from io import UnsupportedOperation
from pathlib import Path
from typing import Dict, List, Optional, Union, Literal, BinaryIO
from tempfile import TemporaryDirectory
from zipfile import ZipFile, is_zipfile
from py7zr import SevenZipFile, is_7zfile
import tarfile as tar
from rarfile import RarFile, is_rarfile

from libacbf.constants import ArchiveTypes
from libacbf.exceptions import EditRARArchiveError, UnsupportedArchive

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
	if isinstance(file, ZipFile):
		return ArchiveTypes.Zip
	elif isinstance(file, SevenZipFile):
		return ArchiveTypes.SevenZip
	elif isinstance(file, tar.TarFile):
		return ArchiveTypes.Tar
	elif isinstance(file, RarFile):
		return ArchiveTypes.Rar

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
	def __init__(self, archive: Union[str, Path, BinaryIO], mode: Literal['r', 'w'] = 'r'):
		self.mode: Literal['r', 'w'] = mode
		self.type: ArchiveTypes = get_archive_type(archive)

		arc = None
		if isinstance(archive, (ZipFile, SevenZipFile, tar.TarFile, RarFile)):
			arc = archive

		if isinstance(archive, str):
			archive = Path(archive).resolve(True)

		if hasattr(archive, "seek"):
			archive.seek(0)

		self.changes: Dict[str, str] = {}

		if mode == 'w' and self.type == ArchiveTypes.Rar:
			raise EditRARArchiveError

		if arc is None:
			if self.type == ArchiveTypes.Zip:
				arc = ZipFile(archive, 'r')
			elif self.type == ArchiveTypes.SevenZip:
				arc = SevenZipFile(archive, 'r')
			elif self.type == ArchiveTypes.Tar:
				if isinstance(archive, (str, Path)):
					arc = tar.open(archive, mode='r')
				else:
					arc = tar.open(fileobj=archive, mode='r')
			elif self.type == ArchiveTypes.Rar:
				arc = RarFile(archive)

		self.archive: Union[ZipFile, SevenZipFile, tar.TarFile, RarFile] = arc

	@property
	def filename(self) -> Optional[str]:
		name = None
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.SevenZip, ArchiveTypes.Rar]:
			name = self.archive.filename
		elif self.type == ArchiveTypes.Tar:
			name = self.archive.name

		if name is not None:
			name = Path(name).name
		return name

	def _get_acbf_file(self) -> Optional[str]:
		acbf_file = None
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

		return acbf_file

	def list_files(self) -> List[str]:
		"""[summary]
		"""
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
			return [x.filename for x in self.archive.infolist() if not x.is_dir()]
		elif self.type == ArchiveTypes.Tar:
			return [x.name for x in self.archive.getmembers() if x.isfile()]
		elif self.type == ArchiveTypes.SevenZip:
			return [x.filename for x in self.archive.list() if not x.is_directory]

	def list_dirs(self) -> List[str]:
		"""[summary]
		"""
		if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
			return [x.filename for x in self.archive.infolist() if x.is_dir()]
		elif self.type == ArchiveTypes.Tar:
			return [x.name for x in self.archive.getmembers() if x.isdir()]
		elif self.type == ArchiveTypes.SevenZip:
			return [x.filename for x in self.archive.list() if x.is_directory]

	def read(self, target: str) -> Optional[bytes]:
		"""Get file as bytes from archive. Defaults to contents of ACBF file.

		Parameters
		----------
		target : str, default=ACBF File
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

	def write(self, target: Union[str, Path], arcname: Optional[str] = None):
		"""Call ``ACBFBook.save()`` or ``ACBFBook.close()`` to apply changes.

		Parameters
		----------
		target : str | Path
			[description]
		arcname : str | None, default=Name of target file
			[description]
		"""
		if self.mode == 'r':
			raise UnsupportedOperation("File is not writeable.")

		if isinstance(target, str):
			target = Path(target)
		target = target.resolve(True)

		if arcname is None:
			arcname = target.name

		self.changes[str(target)] = arcname

	def remove(self, target: Union[str, Path]):
		"""Call ``ACBFBook.save()`` or ``ACBFBook.close()`` to apply changes. Always recursive for
		directories.

		Parameters
		----------
		target : str | Path
			[description]
		"""
		if self.mode == 'r':
			UnsupportedOperation("File is not writeable.")

		if isinstance(target, str):
			target = Path(target)

		files = [Path(x) for x in self.list_files() + self.list_dirs()]
		if not target.is_absolute() and target in files:
			self.changes[str(target)] = ""

	def save(self, file: Union[str, BinaryIO]):
		if self.mode == 'r':
			UnsupportedOperation("File is not writeable.")

		with TemporaryDirectory() as td:
			td = Path(td)

			if len(self.list_files() + self.list_dirs()) > 0:
				self.archive.extractall(td)

			for source, action in self.changes.items():
				action = Path(action)
				action.resolve()
				if action != '' and (td in action.parents or len(action.parents) == 1):
					shutil.copy(source, str(td/action))
				else:
					if source in self.list_files():
						try:
							os.remove(td/source)
						except FileNotFoundError:
							pass
					elif source in self.list_dirs():
						shutil.rmtree(td/source)

			files = [x.relative_to(td) for x in td.rglob('*') if x.is_file()]
			self.archive.close()

			if self.type == ArchiveTypes.Zip:
				with ZipFile(file, 'w') as arc:
					for i in files:
						arc.write(str(td/i), str(i))
				self.archive = ZipFile(file, 'r')
			elif self.type == ArchiveTypes.SevenZip:
				with SevenZipFile(file, 'w') as arc:
					for i in files:
						arc.write(td/i, str(i))
				self.archive = SevenZipFile(file, 'r')
			elif self.type == ArchiveTypes.Tar:
				with tar.open(file, 'w') as arc:
					for i in files:
						arc.add(str(td/i), str(i))
				self.archive = tar.open(file, 'r')

	def close(self):
		"""Close archive file object or remove temporary directory.
		"""
		self.archive.close()

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, traceback):
		self.close()
