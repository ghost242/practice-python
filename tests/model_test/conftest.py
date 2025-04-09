import logging
import os

from uuid import uuid4

import pytest

# from .model_fixtures_v1 import *
# from .model_fixtures_v2 import *

def pytest_sessionstart(session):
    logging.getLogger().setLevel(logging.INFO)
    print("session started")

def pytest_sessionfinish(session, exitstatus):
    print("session finished")

def pytest_generate_tests(metafunc):
    print("generating tests")
    
def pytest_collection(session):
    print("collection started")

def pytest_collection_finish(session):
    print("collection finished")

def pytest_runtestloop(session):
    print("runtest loop started")

def pytest_runtest_setup(item):
    os.environ["TEST_ENV"] = str(uuid4())
    
    print("runtest setup: ", item)

def pytest_runtest_teardown(item, nextitem):
    del os.environ["TEST_ENV"]
    
    print("runtest teardown")

