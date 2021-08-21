import os
import shutil
from io import UnsupportedOperation
from pathlib import Path
from typing import Set, Optional, Union, Literal, BinaryIO
from tempfile import TemporaryDirectory
from zipfile import ZipFile, is_zipfile
from py7zr import SevenZipFile, is_7zfile
from rarfile import RarFile, is_rarfile
import tarfile as tar

from libacbf.constants import ArchiveTypes
from libacbf.exceptions import EditRARArchiveError, UnsupportedArchive


def get_archive_type(file: Union[str, Path, BinaryIO]) -> ArchiveTypes:
    """Get the type of archive.

    Parameters
    ----------
    file : str | pathlib.Path | BinaryIO
        File to check.

    Returns
    -------
    ArchiveTypes(Enum)
        Returns :class:`ArchiveTypes <libacbf.constants.ArchiveTypes>` enum.

    Raises
    ------
    UnsupportedArchive
        Raised if file is not of a supported archive type.
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
    """This can read and write Zip, 7Zip and Tar archives. Rar archives are read-only.

    Notes
    -----
    Writing and creating archives uses the default options for each type. You cannot use this module to change
    compression levels or other options.

    Parameters
    ----------
    file : str | pathlib.Path | BinaryIO
        Archive file to be used.

    mode : 'r' | 'w'
        Mode to open file in. Can be ``'r'`` for read-only or ``'w'`` for read-write. Nothing is overwritten.

    Attributes
    ----------
    archive : zipfile.ZipFile | tarfile.TarFile | py7zr.SevenZipFile | rarfile.RarFile
        The archive being used.

    type : ArchiveTypes
        The type of archive. See enum for possible types.

    mode : 'r' | 'w'
        Mode to open file in. Can be ``'r'`` for read-only or ``'w'`` for read-write. Nothing is overwritten.

    _extract : tempfile.TemporaryDirectory | None
        The contents of the archive are extracted to a temporary directory in write mode only and this is used for
        listing, reading and writing. It is created in the same directory as the archive or, if the path is not found,
        it is created in the system temp directory.

    _arc_path : pathlib.Path | None
        The path to the temporary directory the archive is extracted to in write mode.

    _source : str | Path | BinaryIO
        The file passed in.
    """

    def __init__(self, file: Union[str, Path, BinaryIO], mode: Literal['r', 'w'] = 'r'):
        self._extract = None
        self._arc_path = None
        self._source = file
        self.mode: Literal['r', 'w'] = mode
        self.type: ArchiveTypes = get_archive_type(file)

        if isinstance(file, str):
            file = Path(file).resolve(True)

        if hasattr(file, "seek"):
            file.seek(0)

        if mode == 'w':
            if self.type == ArchiveTypes.Rar:
                raise EditRARArchiveError

        arc = None
        if self.type == ArchiveTypes.Zip:
            arc = ZipFile(file, 'r')
        elif self.type == ArchiveTypes.SevenZip:
            arc = SevenZipFile(file, 'r')
        elif self.type == ArchiveTypes.Tar:
            if isinstance(file, (str, Path)):
                arc = tar.open(file, mode='r')
            else:
                arc = tar.open(fileobj=file, mode='r')
        elif self.type == ArchiveTypes.Rar:
            arc = RarFile(file)

        self.archive: Union[ZipFile, SevenZipFile, tar.TarFile, RarFile] = arc

        if mode == 'w':
            if self.filepath is not None:
                self._extract = TemporaryDirectory(dir=self.filepath.parent)
            else:
                self._extract = TemporaryDirectory()

            self._arc_path = Path(self._extract.name)
            self.archive.extractall(self._arc_path)

    @property
    def filepath(self) -> Optional[Path]:
        """Path to the archive file. Returns ``None`` if it does not have a path.
        """
        name = None
        if self.type in (ArchiveTypes.Zip, ArchiveTypes.SevenZip, ArchiveTypes.Rar):
            name = self.archive.filename
        elif self.type == ArchiveTypes.Tar:
            name = self.archive.name

        if name is not None:
            name = Path(name)
        return name

    @property
    def filename(self) -> Optional[str]:
        """Name of the archive file. Returns ``None`` if it does not have a path.
        """
        return self.filepath.name

    def _get_acbf_file(self) -> Optional[str]:
        """Returns the name of the first file with the ``.acbf`` extension at the root level of the archive or ``None``
        if no file is found.
        """
        acbf_file = None

        if self._arc_path is not None:
            for i in self._arc_path.glob("*.acbf"):
                if i.is_file():
                    acbf_file = i.relative_to(self._arc_path)
                    break
        else:
            if self.type in (ArchiveTypes.Zip, ArchiveTypes.Rar):
                for i in self.archive.infolist():
                    if not i.is_dir() and '/' not in i.filename and i.filename.endswith(".acbf"):
                        acbf_file = i.filename
                        break
            elif self.type == ArchiveTypes.SevenZip:
                self.archive.reset()
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

    def list_files(self) -> Set[str]:
        """Returns a list of all the names of the files in the archive.
        """
        if self._arc_path is not None:
            return {str(x.relative_to(self._arc_path)) for x in self._arc_path.rglob('*') if x.is_file()}
        else:
            if self.type in (ArchiveTypes.Zip, ArchiveTypes.Rar):
                return {x.filename for x in self.archive.infolist() if not x.is_dir()}
            elif self.type == ArchiveTypes.Tar:
                return {x.name for x in self.archive.getmembers() if x.isfile()}
            elif self.type == ArchiveTypes.SevenZip:
                self.archive.reset()
                return {x.filename for x in self.archive.list() if not x.is_directory}

    def list_dirs(self) -> Set[str]:
        """Returns a list of all the directories in the archive.
        """
        if self._arc_path is not None:
            return {str(x.relative_to(self._arc_path)) for x in self._arc_path.rglob('*') if x.is_dir()}
        else:
            if self.type in (ArchiveTypes.Zip, ArchiveTypes.Rar):
                return {x.filename for x in self.archive.infolist() if x.is_dir()}
            elif self.type == ArchiveTypes.Tar:
                return {x.name for x in self.archive.getmembers() if x.isdir()}
            elif self.type == ArchiveTypes.SevenZip:
                self.archive.reset()
                return {x.filename for x in self.archive.list() if x.is_directory}

    def read(self, target: str) -> Optional[bytes]:
        """Get file as bytes from archive.

        Parameters
        ----------
        target : str
            Path relative to root of archive.

        Returns
        -------
        bytes
            Contents of file.
        """
        contents = None

        if self._arc_path is not None:
            with open(self._arc_path / target, 'rb') as file:
                contents = file.read()
        else:
            if self.type in (ArchiveTypes.Zip, ArchiveTypes.Rar):
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

    def write(self, target: Union[str, Path, bytes], arcname: Optional[str] = None):
        """Write file to archive.

        Parameters
        ----------
        target : str | Path | bytes
            File to be written. Reads a file on disk if string or path is passed. Writes data directly if bytes is
            passed.

        arcname : str, default=Name of target file
            Name of file in archive.
        """
        if self.mode == 'r':
            raise UnsupportedOperation("Archive is not writeable.")

        if isinstance(target, str):
            target = Path(target)

        contents = None

        if isinstance(target, Path):
            target = target.resolve(True)
            with open(target, 'rb') as src:
                contents = src.read()

        if isinstance(target, bytes):
            contents = target

        if arcname is None:
            if isinstance(target, bytes):
                raise AttributeError("`arcname` is required if `target` is bytes.")
            arcname = target.name

        if not (self._arc_path / arcname).resolve().is_relative_to(self._arc_path.resolve()):
            raise ValueError("`arcname` does not resolve to a file inside the archive.")

        os.makedirs(self._arc_path / Path(arcname).parent, exist_ok=True)

        with open(self._arc_path / arcname, 'wb') as file:
            file.write(contents)

    def delete(self, target: Union[str, Path], recursive: bool = False):
        """File to delete from archive.

        Parameters
        ----------
        target : str | Path
            Path of file to delete relative to root of archive.

        recursive : bool, default=False
            Whether to remove directories recursively.
        """
        if self.mode == 'r':
            UnsupportedOperation("Archive is not writeable.")

        if isinstance(target, str):
            target = Path(target)

        if isinstance(target, Path):
            target = (self._arc_path / target).resolve(True)

        if not target.resolve().is_relative_to(self._arc_path.resolve()):
            raise ValueError("`target` does not resolve to a file inside the archive.")

        if target.is_file():
            try:
                os.remove(self._arc_path / target)
            except FileNotFoundError:
                pass
        else:
            if recursive:
                shutil.rmtree(self._arc_path / target)
            else:
                try:
                    os.rmdir(self._arc_path / target)
                except FileNotFoundError:
                    pass

    def close(self):
        """Close archive file. Save changes if writeable.
        """
        self.archive.close()

        if self._arc_path is not None:

            if self.type == ArchiveTypes.Zip:
                with ZipFile(self._source, 'w') as arc:
                    for i in self.list_files():
                        arc.write(self._arc_path / i, i)

            elif self.type == ArchiveTypes.SevenZip:
                with SevenZipFile(self._source, 'w') as arc:
                    for i in self.list_files():
                        arc.write(self._arc_path / i, i)

            elif self.type == ArchiveTypes.Tar:
                with tar.open(self._source, 'w') as arc:
                    for i in self.list_files():
                        arc.add(self._arc_path / i, i)

            self._extract.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is not None:
            self.archive.close()
            self._extract.cleanup()
        else:
            self.close()
