
import re
import string
from typing import Any
from typing import List
from typing import Optional
from typing import Protocol
from typing import TypeVar

from .mixin import Mixin

class IsTemplatePre311(Protocol):

    delimiter: str
    idpattern: str
    braceidpattern: Optional[str]
    flags: int
    pattern: re.Pattern[str]
    template: str
    def safe_substitute(self: Any) -> Optional[str]:
        ...
    def substitute(self: Any) -> Optional[str]:
        ...

_T = TypeVar('_T', bound=string.Template)

class TemplateGetIdentifiersMixin(Mixin[Any]):

    delimiter: str
    idpattern: str
    braceidpattern: Optional[str]
    flags: int
    pattern: re.Pattern[str]
    template: str
    def safe_substitute(self: object) -> Optional[str]:
        ...
    def substitute(self: object) -> Optional[str]:
        ...
    def get_identifiers(self: IsTemplatePre311) -> List[str]:
        ...
    @classmethod
    def extend_with(cls: type[IsTemplatePre311], instance: _T) -> _T:
        ...
