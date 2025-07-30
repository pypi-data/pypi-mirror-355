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


from abc import ABC, abstractmethod
from typing import Optional


class PoolIdAttr(ABC):
    """Define a protocol class for managing the setting and getting of resource pool IDs."""

    @abstractmethod
    def set_pool_id(self, pool_id: Optional[str]):
        """Set the resource pool ID.

        Args:
            pool_id (Optional[str]): Resource pool ID string. Maybe None.
        """

    @abstractmethod
    def get_pool_id(self) -> Optional[str]:
        """Get the resource pool ID.

        Returns:
            Optional[str]: Return resource pool ID string. If not set, return None。
        """
