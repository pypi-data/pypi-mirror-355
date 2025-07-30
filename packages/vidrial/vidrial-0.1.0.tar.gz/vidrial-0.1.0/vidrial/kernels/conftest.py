import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--heavy", action="store_true", default=False, help="run heavy tests"
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "heavy: mark test as heavy to run"
    )

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--heavy"):
        # --heavy given in cli: do not skip heavy tests
        skip_heavy = pytest.mark.skip(reason="need --heavy option to run")
        for item in items:
            if "heavy" in item.keywords:
                item.add_marker(skip_heavy)
    else:
        # --heavy not given in cli: skip heavy tests
        return 