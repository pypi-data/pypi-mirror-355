#  Copyright © 2025 China Mobile (SuZhou) Software Technology Co.,Ltd
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
from collections.abc import Sequence
from typing import Callable, Optional, Union

from pydantic import SecretStr


class _NoDefaultType:
    """Type to indicate no default value is provided."""


_NoDefault = _NoDefaultType()


# This function is derived from 'langchain' (MIT License)
# Original source: https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/utils/utils.py#L427
# -L468
# Copyright (c) LangChain, Inc.

def secret_from_env(
        key: Union[str, Sequence[str]],
        /,
        *,
        default: Union[str, _NoDefaultType, None] = _NoDefault,
        error_message: Optional[str] = None,
) -> Union[Callable[[], Optional[SecretStr]], Callable[[], SecretStr]]:
    """Secret from env.

    Args:
        key: The environment variable to look up.
        default: The default value to return if the environment variable is not set.
        error_message: the error message which will be raised if the key is not found
            and no default value is provided.
            This will be raised as a ValueError.

    Returns:
        factory method that will look up the secret from the environment.
    """

    def get_secret_from_env() -> Optional[SecretStr]:
        """Get a value from an environment variable."""
        if isinstance(key, (list, tuple)):
            for k in key:
                if k in os.environ:
                    return SecretStr(os.environ[k])
        if isinstance(key, str) and key in os.environ:
            return SecretStr(os.environ[key])
        if isinstance(default, str):
            return SecretStr(default)
        if default is None:
            return None
        if error_message:
            raise ValueError(error_message)
        msg = (
            f"Did not find {key}, please add an environment variable"
            f" `{key}` which contains it, or pass"
            f" `{key}` as a named parameter."
        )
        raise ValueError(msg)

    return get_secret_from_env
