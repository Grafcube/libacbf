import os
import pytest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def pytest_runtest_logreport(report):
    if report.failed and report.when in ('setup', 'teardown'):
        raise pytest.UsageError("Errors during collection, aborting")


@pytest.fixture(scope="session")
def results():
    res = Path(__file__).parent / "results"
    os.makedirs(res, exist_ok=True)

    with ZipFile(res / "test_create.fail.cbz", 'w', ZIP_DEFLATED, compresslevel=9) as zip:
        for file in (res.parent / "samples").rglob('*'):
            if file.is_file() and not file.suffix == ".acbf":
                name = file.relative_to(res.parent / "samples")
                zip.write(file, name)

    return res


@pytest.fixture(scope="session")
def results_body(results):
    res = results / "test_body"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_bookinfo(results):
    res = results / "test_metadata/book_info"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_publishinfo(results):
    res = results / "test_metadata/publish_info"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_documentinfo(results):
    res = results / "test_metadata/document_info"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_edit(results):
    res = results / "test_edit"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_edit_convert(results):
    res = results / "test_convert"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_edit_body(results_edit):
    res = results_edit / "test_body"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_edit_data(results_edit):
    res = results_edit / "test_data"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_edit_bookinfo(results_edit):
    res = results_edit / "test_meta/test_bookinfo"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_edit_publishinfo(results_edit):
    res = results_edit / "test_meta/test_publishinfo"
    os.makedirs(res, exist_ok=True)
    return res


@pytest.fixture(scope="session")
def results_edit_documentinfo(results_edit):
    res = results_edit / "test_meta/test_documentinfo"
    os.makedirs(res, exist_ok=True)
    return res


def get_au_op(i):
    new_op = i.__dict__.copy()
    new_op["activity"] = new_op["_activity"].name if new_op["_activity"] is not None else None
    new_op.pop("_activity")
    new_op["lang"] = new_op["_lang"]
    new_op.pop("_lang")
    new_op["first_name"] = new_op["_first_name"]
    new_op.pop("_first_name")
    new_op["last_name"] = new_op["_last_name"]
    new_op.pop("_last_name")
    new_op["nickname"] = new_op["_nickname"]
    new_op.pop("_nickname")
    return new_op
