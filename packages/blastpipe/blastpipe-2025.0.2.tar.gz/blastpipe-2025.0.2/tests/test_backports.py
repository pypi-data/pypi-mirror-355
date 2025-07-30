# noqa: INP001
"""Tests for backported code."""
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
import string

from hypothesis import given
from hypothesis import strategies as st

# pylint: disable=import-error
import blastpipe.backports


# pylint: disable=invalid-name
@given(instance=st.builds(string.Template, st.text()))
def test_fuzz_TemplateGetIdentifiersMixin_extend_with(instance: string.Template) -> None:
    """Test extension of arbitrary :py:class:`string.Template` text.

    :param instance: Text Template
    :type instance: string.Template
    """
    blastpipe.backports.TemplateGetIdentifiersMixin.extend_with(instance=instance)
