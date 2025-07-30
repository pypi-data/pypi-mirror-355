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


import logging
from datetime import datetime
from typing import Optional, TypeVar

from dateutil import parser

from ecl_mcp_server.attr import PoolIdAttr
from ecl_mcp_server.context import context

from .thirdparty import secret_from_env

__all__ = ["secret_from_env", "serialize_datetime", "deserialize_datetime", "deserialize_datetime_optional", "common_logger", "check_poolid"]

common_logger = logging.getLogger("common")


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime object to ISO format string

    Args:
        dt: datetime object to serialize

    Returns:
        String in 'YYYY-MM-DD HH:MM:SS' format
    """
    return dt.isoformat(sep=" ", timespec="seconds")


def deserialize_datetime(datetime_string: str | datetime) -> datetime:
    """Deserialize string or datetime object to datetime object

    Args:
        datetime_string: string or datetime object to deserialize

    Returns:
        Parsed datetime object

    Raises:
        ValueError: if input is None or in invalid format
    """
    if datetime_string is None:
        raise ValueError("datetime field cannot be None")
    if isinstance(datetime_string, datetime):
        return datetime_string
    try:
        return datetime.fromisoformat(datetime_string)
    except ValueError:
        return parser.parse(datetime_string)


def deserialize_datetime_optional(v: str | datetime | None) -> Optional[datetime]:
    """Optional datetime deserialization that allows None input

    Args:
        v: string, datetime object or None to deserialize

    Returns:
        Parsed datetime object or None
    """
    if v is None:
        return None
    return deserialize_datetime(v)


T = TypeVar("T")


def check_poolid(request: PoolIdAttr):
    """Check and set the resource pool ID in the request.

    If the resource pool ID in the request is empty, try to get the preferred pool ID
    from context and set it. If the preferred pool ID in context is also empty,
    raise an exception.

    Args:
        request (PoolIdAttr): Object containing resource pool ID attributes.

    Raises:
        ValueError: When resource pool ID is not specified.
    """
    if request.get_pool_id() is None:
        if context.preferredPoolId is not None:
            request.set_pool_id(context.preferredPoolId)
        else:
            raise ValueError("poolId must be specified")
