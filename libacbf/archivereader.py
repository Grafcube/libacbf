import os
import shutil
from io import UnsupportedOperation
from pathlib import Path
from typing import Dict, List, Optional, Union, Literal, BinaryIO
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
    file : str | Path | BinaryIO
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
    file : str | Path | BinaryIO
        Archive file to be used.

    mode : 'r' | 'w'
        Mode to open file in. Can be ``'r'`` for read-only or ``'w'`` for read-write. Nothing is overwritten.

    Attributes
    ----------
    archive : zipfile.ZipFile | tarfile.TarFile | py7zr.SevenZipFile | rarfile.RarFile
        The archive being used.

    type : ArchiveTypes
        The type of archive. See enum for possible types.

    changes : Dict[str, str]
        Changes to be applied on save. Writing and deleting files in the archive are not done immediately. They keys
        are the names of the files in the archive and the values are the target files to be written or ``''`` if it is
        to be deleted.
    """

    def __init__(self, file: Union[str, Path, BinaryIO], mode: Literal['r', 'w'] = 'r'):
        self.mode: Literal['r', 'w'] = mode
        self.type: ArchiveTypes = get_archive_type(file)

        arc = None
        if isinstance(file, (ZipFile, SevenZipFile, tar.TarFile, RarFile)):
            arc = file

        if isinstance(file, str):
            file = Path(file).resolve(True)

        if hasattr(file, "seek"):
            file.seek(0)

        self.changes: Dict[str, str] = {}

        if mode == 'w' and self.type == ArchiveTypes.Rar:
            raise EditRARArchiveError

        if arc is None:
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

    @property
    def filename(self) -> Optional[str]:
        """Name of the archive file. Returns ``None`` if it does not have a path.
        """
        name = None
        if self.type in [ArchiveTypes.Zip, ArchiveTypes.SevenZip, ArchiveTypes.Rar]:
            name = self.archive.filename
        elif self.type == ArchiveTypes.Tar:
            name = self.archive.name

        if name is not None:
            name = Path(name).name
        return name

    def _get_acbf_file(self) -> Optional[str]:
        """Returns the name of the first file with the ``.acbf`` extension at the root level of the archive.
        """
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
        """Returns a list of all the names of the files in the archive.
        """
        if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
            return [x.filename for x in self.archive.infolist() if not x.is_dir()]
        elif self.type == ArchiveTypes.Tar:
            return [x.name for x in self.archive.getmembers() if x.isfile()]
        elif self.type == ArchiveTypes.SevenZip:
            self.archive.reset()
            return [x.filename for x in self.archive.list() if not x.is_directory]

    def list_dirs(self) -> List[str]:
        """Returns a list of all the directories in the archive.
        """
        if self.type in [ArchiveTypes.Zip, ArchiveTypes.Rar]:
            return [x.filename for x in self.archive.infolist() if x.is_dir()]
        elif self.type == ArchiveTypes.Tar:
            return [x.name for x in self.archive.getmembers() if x.isdir()]
        elif self.type == ArchiveTypes.SevenZip:
            self.archive.reset()
            return [x.filename for x in self.archive.list() if x.is_directory]

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
        """Write file to archive. Call :meth:`save()` to apply changes.

        Parameters
        ----------
        target : str | Path
            Path of file to be written.
        arcname : str, default=Name of target file
            Name of file in archive.
        """
        if self.mode == 'r':
            raise UnsupportedOperation("File is not writeable.")

        if isinstance(target, str):
            target = Path(target)
        target = target.resolve(True)

        if arcname is None:
            arcname = target.name

        self.changes[arcname] = str(target)

    def delete(self, target: Union[str, Path]):
        """File to delete from archive. Call :meth:`save()` to apply changes. Always recursive for directories.

        Parameters
        ----------
        target : str | Path
            Path of file to delete relative to root of archive.
        """
        if self.mode == 'r':
            UnsupportedOperation("File is not writeable.")

        if isinstance(target, str):
            target = Path(target)

        files = [Path(x) for x in self.list_files() + self.list_dirs() + list(self.changes.keys())]
        if not target.is_absolute() and target in files:
            self.changes[str(target)] = ''
        else:
            raise FileNotFoundError("File not in archive.")

    def save(self, file: Union[str, BinaryIO]):
        """Saves all changes.

        Parameters
        ----------
        file : str | BinaryIO
            Path or file object to save the archive to.
        """
        if self.mode == 'r':
            UnsupportedOperation("File is not writeable.")

        with TemporaryDirectory() as td:
            td = Path(td)

            if len(self.list_files() + self.list_dirs()) > 0:
                self.archive.extractall(td)

            for action, source in self.changes.items():
                action = Path(action)
                action.resolve()
                os.makedirs(td / action.parent, exist_ok=True)
                if source != '':
                    shutil.copy(source, td / action)
                else:
                    if source in self.list_files():
                        try:
                            os.remove(td / source)
                        except FileNotFoundError:
                            pass
                    elif source in self.list_dirs():
                        shutil.rmtree(td / source)

            self.changes.clear()
            files = [x.relative_to(td) for x in td.rglob('*') if x.is_file()]
            self.archive.close()

            if self.type == ArchiveTypes.Zip:
                with ZipFile(file, 'w') as arc:
                    for i in files:
                        arc.write(str(td / i), str(i))
                self.archive = ZipFile(file, 'r')
            elif self.type == ArchiveTypes.SevenZip:
                with SevenZipFile(file, 'w') as arc:
                    for i in files:
                        arc.write(td / i, str(i))
                self.archive = SevenZipFile(file, 'r')
            elif self.type == ArchiveTypes.Tar:
                with tar.open(file, 'w') as arc:
                    for i in files:
                        arc.add(str(td / i), str(i))
                self.archive = tar.open(file, 'r')

    def close(self):
        """Discard changes and close archive file.
        """
        self.changes.clear()
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
