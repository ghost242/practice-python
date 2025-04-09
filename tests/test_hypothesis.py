import logging
import os

from pytest import fixture
from hypothesis import given, settings, Verbosity
from hypothesis.strategies import integers, lists


def add(x, y):
    return x + y


def sub(x, y):
    return x - y

@fixture()
def sample():
    return 1234

@settings(max_examples=100, print_blob=True, verbosity=Verbosity.verbose)
@given(integers(), integers())
def test_add(t, s):
    logging.info(t)
    logging.info(s)
    assert add(t, s) == t + s

@given(integers(), integers())
def test_sub(t, s):
    assert sub(t, s) == t - s

def test_sub_zero(sample):
    assert sub(sample, sample) == sample - sample
    