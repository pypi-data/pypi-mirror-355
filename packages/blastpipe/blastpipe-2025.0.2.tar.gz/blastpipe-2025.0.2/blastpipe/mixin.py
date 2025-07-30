"""Mixin ABC, Generic, and helper function."""

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
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Generic
from typing import TypeVar

# pylint: disable=import-error
from . import public


# pylint: disable=too-few-public-methods
@public
class BaseMixin(ABC):
    """Abstract mixin class"""

    @classmethod
    @abstractmethod
    def extend_with(cls: Any, instance: Any) -> Any:
        """extend the instance with the mixin cls"""


_T = TypeVar('_T', bound='BaseMixin')


@public
class Mixin(Generic[_T], BaseMixin):
    """Generic mixin class"""


@public
def mixin(cls: Any, base: Any) -> Any:
    """Helper function to extend the class with the base"""

    def __wrapper(*args: Any, **kwargs: Any) -> Any:
        """decorator"""
        return cls.extend_with(base(*args, **kwargs))

    return __wrapper
