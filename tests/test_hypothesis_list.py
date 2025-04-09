"""
Hypothesis 패키지를 이용하는 테스트 코드에 대한 실험코드
"""
import logging

from itertools import product

from hypothesis import Verbosity, given, settings
import hypothesis.strategies as st


def func(a, b):
    return a + b


@settings(verbosity=Verbosity.verbose, max_examples=500)
@given(
    st.lists(st.integers(min_value=0, max_value=5), min_size=2),
    st.lists(st.integers(min_value=10, max_value=14), min_size=2),
)
def test_func(val1, val2):
    assert val1 <= val2
    
    for v1, v2 in product(val1, val2):
        assert v1 <= v2
