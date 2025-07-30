# Copyright (c) 2025 Yoann Piétri
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from enum import Enum
from typing import Any
from functools import total_ordering


@total_ordering
class LaserClass(Enum):
    """An enumeration of laser classes, with ordering.

    The enumeration is equipped with a total ordering that
    can be used to compare a class with either another class
    such that

    >>> LaserClass.ONE < LaserClass.THREE_R
    True

    >>> LaserClass.TWO_M >= THREE_B
    False

    but also compare to a an int

    >>> LaserClass.THREE == 3
    True

    >>> LaserClass.TWO_M < 3
    True
    """

    ONE = "1", 1, 1  #: Class 1
    ONE_M = "1M", 2, 1  #: Class 1M
    TWO = "2", 3, 2  #: Class 2
    TWO_M = "2M", 4, 2  #: Class 2M
    THREE_R = "3R", 5, 3  #: Class 3R
    THREE_B = "3B", 6, 3  #: Class 3B
    FOUR = "4", 7, 4  #: Class 4

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def _is_valid_operand(self, other: Any) -> bool:
        """Check that the other operand of a comparison is valid.

        Comparisons are valid with LaserClass and int instances.

        Args:
            other (Any): the other operand.

        Returns:
            bool: wether the other operand is valid or not.
        """
        return isinstance(other, (LaserClass, int))

    def __init__(self, _: str, order: int, overall_class: int):
        """Store the absolute order and the overall class.

        Args:
            _ (str): the name of the class, already stored in new.
            order (int): the absolute order of the class.
            overall_class (int): the overall class for each class.
        """
        self._order_ = order
        self._overall_class_ = overall_class

    def __str__(self):
        return self.value

    def __lt__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        if isinstance(other, int):
            return self._overall_class_ < other
        return self._order_ < other._order_

    def __eq__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        if isinstance(other, int):
            return self._overall_class_ == other
        return self._order_ == other._order_
