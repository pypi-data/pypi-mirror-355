from typing import Annotated
from typing import Any
from typing import Callable
from typing import Optional
from typing import Tuple

from . import public

TAIL_CALL: Tuple[()] = ...

@public
def async_tail_call(
    active: bool = ...,
) -> Annotated[Callable[..., Any], Annotated[Optional[Tuple[()]], '@tail_call()']]:
    ...
