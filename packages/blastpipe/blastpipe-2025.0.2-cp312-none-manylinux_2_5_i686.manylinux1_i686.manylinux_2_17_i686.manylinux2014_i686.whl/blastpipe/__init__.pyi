from typing import Annotated
from typing import Any

def public(obj: Any) -> Annotated[Any, '__all__.__contains__(__name__)']:
    ...



