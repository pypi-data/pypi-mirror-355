"""Sequence manipulation."""

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
from __future__ import annotations

import asyncio
from typing import Set

# pylint: disable=import-error
from . import public
from .tailcall import async_tail_call


async def _chr_union(*args: int) -> Set[str]:
    """creates a set of all characters in the union of the given chars"""
    chars = set()
    if len(args) == 2 and all(map(isinstance, args, (int,) * len(args))):
        start, stop = args
        chars |= {chr(i) for i in range(start, stop)}
        return chars
    for i in args:
        if isinstance(i, int):
            chars |= {chr(i)}
        elif len(i) == 2 and all(map(isinstance, i, (int,) * len(i))):
            return i
        else:
            raise TypeError(f'Expected Sequence or int, got {type(i)}')
    return chars


@public
def chr_union(*args: int) -> Set[str]:
    """Wraps an asynchronous sequence of int ranges or ints into a set of str
    :return: a set of chr()
       # 1. range(start=args[0], stop=args[1])
          * OR
       # 2. chr(arg[n] if type(arg[n])==int) | chr_union(arg[:2])
    :raises: TypeError
        if not a sequence of start,stop pairs and ints, an int, or a start, stop pair
    """
    return asyncio.run(async_tail_call()(_chr_union)(*args))
