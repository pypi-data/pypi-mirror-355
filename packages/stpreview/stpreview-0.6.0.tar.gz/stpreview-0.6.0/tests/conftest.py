import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--shareddata",
        action="store_true",
        default=False,
        help="run tests on shared data",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--shareddata"):
        return
    skip_shareddata = pytest.mark.skip(reason="need --shareddata option to run")
    for item in items:
        if "shareddata" in item.keywords:
            item.add_marker(skip_shareddata)
