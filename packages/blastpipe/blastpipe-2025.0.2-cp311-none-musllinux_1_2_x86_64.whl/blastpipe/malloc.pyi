from typing import Any
from typing import Callable
from typing import Dict
from typing import Hashable
from typing import Optional

from . import public

@public
def total_size(
    obj: Hashable,
    handlers: Optional[Dict[Any, Callable[..., Any]]] = ...,
    verbose: bool = ...,
) -> int:
    ...
