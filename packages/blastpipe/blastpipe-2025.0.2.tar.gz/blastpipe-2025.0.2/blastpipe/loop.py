"""Utility functions for while loops"""

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

from contextlib import suppress
from typing import Any
from typing import Callable
from typing import Optional
from typing import Tuple
from typing import Type

# pylint: disable=import-error
from . import public


@public
def while_raised(
    exc_types: Tuple[Type[Exception]],
    target: Callable[..., Any],
    /,
    *args: Any,
    implicit_break: bool = True,
) -> Optional[Any]:
    """Repeats a target function while suppressing exceptions provided.
    This is a convenience wrapper around :py:func:`contextlib.suppress`.
    :param exc_types: The exception types to suppress.
    :type  exc_types: Tuple[Type[Exception]]
    :param target: The function to repeat.
    :type  target: Callable
    :param implicit_break: Whether to implicitly break out of the loop.
    :type  implicit_break: bool, defaults to True
    :return: The return value of the target function.
    """
    while True:
        with suppress(*exc_types):
            if implicit_break:
                return target(*args)
            target(*args)
            break
    return None
