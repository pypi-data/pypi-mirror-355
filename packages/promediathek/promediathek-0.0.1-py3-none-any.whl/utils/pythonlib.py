from typing import Generic, Optional, TypeVar

from builtins import type
from collections.abc import Callable

T = TypeVar("T")
RT = TypeVar("RT")

# This Code is from https://github.com/python/cpython/issues/89519#issuecomment-2136981592
# Used because @classmethode @property was removed in 3.13 for ProDB


# noinspection PyPep8Naming
class classproperty(Generic[T, RT]):
    """
    Class property attribute (read-only).

    Same usage as @property, but taking the class as the first argument.

        Class C:
            @classproperty
            def x(cls):
                return 0

        Print(C.x)    # 0
        print(C().x)  # 0
    """

    def __init__(self, func: Callable[[type[T]], RT]) -> None:
        # For using `help(...)` on instances in Python >= 3.9.
        self.__doc__ = func.__doc__
        # noinspection PyUnresolvedReferences
        self.__module__ = func.__module__
        self.__name__ = func.__name__
        self.__qualname__ = func.__qualname__
        # Consistent use of __wrapped__ for wrapping functions.
        self.__wrapped__: Callable[[type[T]], RT] = func

    def __set_name__(self, owner: type[T], name: str) -> None:
        # Update based on class context.
        self.__module__ = owner.__module__
        self.__name__ = name
        self.__qualname__ = owner.__qualname__ + "." + name

    def __get__(self, instance: Optional[T], owner: Optional[type[T]] = None) -> RT:
        if owner is None:
            owner = type(instance)
        return self.__wrapped__(owner)
