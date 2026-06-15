import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def pytest_configure():
    # Unit tests must never spend API credits or depend on external availability.
    os.environ["SOLAR_ANALYSIS_ENABLED"] = "false"
