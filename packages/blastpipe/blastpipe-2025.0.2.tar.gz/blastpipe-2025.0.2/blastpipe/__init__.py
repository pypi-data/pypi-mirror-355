"""blastpipe: A utility library for modern Python."""

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
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version
from typing import Annotated
from typing import Any

try:
    __version__ = version('blastpipe')
except PackageNotFoundError:  # pragma: no cover
    pass


def public(obj: Any) -> Annotated[Any, '__all__.__contains__(__name__)']:
    """Declares an object as public."""
    mod = sys.modules[obj.__module__]
    # pylint: disable=unnecessary-dunder-call
    if hasattr(mod, '__all__'):
        mod.__all__.append(obj.__name__)
    else:
        mod.__setattr__('__all__', [obj.__name__])
    return obj
