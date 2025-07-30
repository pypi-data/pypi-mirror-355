from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Generic
from typing import TypeVar

from . import public

@public
class BaseMixin(ABC):

    @classmethod
    @abstractmethod
    def extend_with(cls: Any, instance: Any) -> Any:
        ...

_T = TypeVar('_T', bound=BaseMixin)

@public
class Mixin(Generic[_T], BaseMixin):  # type: ignore[misc]
    ...

@public
def mixin(cls: Any, base: Any) -> Any:
    ...
