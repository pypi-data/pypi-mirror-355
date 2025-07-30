"""Utility for tail call optimization."""

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

import functools
from typing import Annotated
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Optional
from typing import Tuple

# pylint: disable=import-error
from . import public

TAIL_CALL: Tuple[()] = ()


@public
def async_tail_call(
    active: bool = True,
) -> Annotated[Callable[..., Any], Annotated[Optional[Tuple[()]], '@tail_call()']]:
    """Async tail_call decorator.
    :param active: Whether to activate async tail call optimization.
    """

    def __wrapper(func: Callable[..., Any]) -> Optional[Callable[..., Any]]:
        """decorator"""

        async def __trampoline(*args: Any, **_: Mapping[Any, Any]) -> Tuple[Any, ...]:
            """Tail call optimization."""
            while args.__class__ is tuple:
                args = await func(*args)
            return args

        if active:
            functools.update_wrapper(__trampoline, func)
            return __trampoline
        return None

    return __wrapper
