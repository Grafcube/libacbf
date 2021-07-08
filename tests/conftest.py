import os
from pathlib import Path
import pytest
from libacbf import ACBFBook
from tests.testres import samples

dir = Path("tests/results/")

def pytest_addoption(parser):
	parser.addoption("--sample", action="store", default="cbz")

def pytest_runtest_logreport(report):
	if report.failed and report.when in ('setup', 'teardown'):
		raise pytest.UsageError("Errors during collection, aborting")

@pytest.fixture(scope="session")
def book_path(pytestconfig) -> str:
	path = pytestconfig.getoption("sample")
	if path in samples.keys():
		path = samples[path]
	return path

@pytest.fixture(scope="session", autouse=True)
def make_dir(book_path):
	os.makedirs(dir/Path(book_path).name, exist_ok=True)

@pytest.fixture(scope="session")
def read_books(book_path):
	book = (dir/Path(book_path).name, ACBFBook(book_path, 'r'))
	yield book
	book[1].close()

@pytest.fixture(scope="session")
def edit_dir(book_path):
	edit_dir = dir/Path(book_path).name/"editor"
	os.makedirs(edit_dir, exist_ok=True)
	return edit_dir

def get_au_op(i):
	new_op = i.__dict__.copy()
	new_op.pop("_element")
	new_op["activity"] = new_op["_activity"].name if new_op["_activity"] is not None else None
	new_op.pop("_activity")
	new_op["lang"] = new_op["_lang"]
	new_op.pop("_lang")
	new_op["first_name"] = new_op["_first_name"]
	new_op.pop("_first_name")
	new_op["last_name"] = new_op["_last_name"]
	new_op.pop("_last_name")
	return new_op
