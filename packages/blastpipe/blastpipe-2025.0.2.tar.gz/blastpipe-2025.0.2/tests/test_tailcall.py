# noqa: INP001
"""Tail call optimization tests"""
# Copyright 2023 Ross J. Duff MSc
# The copyright holder licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import typing

import pytest
from hypothesis import given
from hypothesis import strategies as st

# pylint: disable=import-error
from blastpipe.sequence import chr_union
from blastpipe.tailcall import async_tail_call


@given(active=st.booleans())
def test_fuzz_async_tail_call(active: bool) -> None:
    """This test code was written by the `hypothesis.extra.ghostwriter` module"""
    async_tail_call(active=active)


def test_chr_union_range() -> None:
    """Test chr_union with a range"""
    assert chr_union((32, 35)) == {' ', '!', '"'}
    assert chr_union(32) == {' '}


@st.composite
def bad_input(draw: typing.Any) -> typing.Tuple[st.SearchStrategy[typing.Any], ...]:
    """Test bad input for chr_union"""
    return (
        draw(st.lists(st.floats())),
        draw(st.lists(st.text())),
        draw(st.lists(st.functions())),
        draw(st.lists(st.booleans())),
        draw(st.floats()),
        draw(st.text()),
        draw(st.functions()),
        draw(st.booleans()),
    )


@given(args=bad_input())
def test_fuzz_bad_input_chr_union(args: typing.Tuple[typing.Any]) -> None:
    """Test bad input for chr_union"""
    with pytest.raises(TypeError):
        _ = chr_union(args)
