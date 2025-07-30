# SPDX-FileCopyrightText: Contributors to the Power Grid Model project <powergridmodel@lfenergy.org>
#
# SPDX-License-Identifier: MPL-2.0

"""Misc utils"""

from collections.abc import Sequence
from typing import Type, get_type_hints

import numpy as np


def is_sequence(seq):
    """
    Returns True for lists, tuples, sets, arrays
    Return False for strings, dicts
    """
    if isinstance(seq, str):
        return False

    if isinstance(seq, (np.ndarray, set)):
        return True
    return isinstance(seq, Sequence)


def get_inherited_attrs(cls: Type, *private_attributes):
    """
    Get the attribute from the object and all its parents
    """

    # The extras are needed for annotated types like NDArray3
    retrieved_attributes = get_type_hints(cls, include_extras=True)
    retrieved_attributes = {attr: type for attr, type in retrieved_attributes.items() if not attr.startswith("_")}

    for private_attr in private_attributes:
        for parent in reversed(list(cls.__mro__)):
            attr_dict = retrieved_attributes.get(private_attr, {})
            attr_dict.update(getattr(parent, private_attr, {}))
            retrieved_attributes[private_attr] = attr_dict

    return retrieved_attributes
