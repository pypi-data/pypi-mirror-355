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


class SingletonBase:
    """Base class for singleton pattern, ensures only one instance per subclass

    Implements singleton pattern by overriding __new__ method. All subclasses will share
    the same instance. Uses class-level _instances dictionary to store instances of each
    singleton class.

    Example:
        >>> class MySingleton(SingletonBase):
        ...     pass
        >>> a = MySingleton()
        >>> b = MySingleton()
        >>> a is b
        True
    """

    _instances = {}

    def __new__(cls, *args, **kwargs):
        """Create or return the singleton instance of the class

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The singleton instance of the class
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]
