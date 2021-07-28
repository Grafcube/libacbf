import os
import pytest
from pathlib import Path
from libacbf import ACBFBook
from libacbf.exceptions import EditRARArchiveError

edit_dir = Path("tests/results/create/")
os.makedirs(edit_dir, exist_ok=True)


def test_create_acbf():
    with ACBFBook(edit_dir / "test_create.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Create", "en")
        book.save(overwrite=True)
        book.Metadata.book_info.edit_annotation("This was created by a test.\nACBF XML File", "en")


def test_create_cbz():
    with ACBFBook(edit_dir / "test_create.cbz", 'w') as book:
        book.Metadata.book_info.edit_title("Test Create", "en")
        book.save(overwrite=True)
        book.Metadata.book_info.edit_annotation("This was created by a test.\nZip Archive.", "en")


def test_create_cb7():
    with ACBFBook(edit_dir / "test_create.cb7", 'w', archive_type="SevenZip") as book:
        book.Metadata.book_info.edit_title("Test Create", "en")
        book.save(overwrite=True)
        book.Metadata.book_info.edit_annotation("This was created by a test.\n7Zip Archive.", "en")


def test_create_cbt():
    with ACBFBook(edit_dir / "test_create.cbt", 'w', archive_type="Tar") as book:
        book.Metadata.book_info.edit_title("Test Create", "en")
        book.save(overwrite=True)
        book.Metadata.book_info.edit_annotation("This was created by a test.\nTar Archive.", "en")


def test_create_cbr():
    with pytest.raises(EditRARArchiveError):
        with ACBFBook(edit_dir / "test_create.cbr", 'w', archive_type="Rar") as _:
            pass
