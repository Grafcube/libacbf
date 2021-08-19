import os
import pytest
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption("--abs", action="store", default=None)


def pytest_runtest_logreport(report):
    if report.failed and report.when in ('setup', 'teardown'):
        raise pytest.UsageError("Errors during collection, aborting")


@pytest.fixture(scope="session")
def abspath(pytestconfig):
    return pytestconfig.getoption("abs")


@pytest.fixture(scope="session")
def results():
    res = Path("tests/results")
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
