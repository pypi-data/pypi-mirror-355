from typing import Any
from typing import Callable
from typing import Optional
from typing import Tuple
from typing import Type

from . import public

@public
def while_raised(
    exc_types: Tuple[Type[Exception]],
    target: Callable[..., Any],
    /,
    *args: Any,
    implicit_break: bool = ...,
) -> Optional[Any]:
    ...
