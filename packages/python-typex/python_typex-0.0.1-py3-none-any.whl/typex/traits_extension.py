##########################################################################
# NSAp - Copyright (C) CEA, 2025
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

import torch

import traits.api as traits
from collections.abc import Sequence


class Int(traits.BaseInt):
    def validate(self, objekt, name, value):
        if isinstance(value, bool):
            self.error(objekt, name, value)
        return super().validate(objekt, name, value)


class Float(traits.BaseFloat):
    def validate(self, objekt, name, value):
        if isinstance(value, int):
            self.error(objekt, name, value)
        return super().validate(objekt, name, value)


class Tuple(traits.BaseTuple):
    def validate(self, objekt, name, value):
        if isinstance(value, list):
            value = tuple(value)
        return super().validate(objekt, name, value)


class Tensor(traits.TraitType):
    def validate(self, objekt, name, value):
        """Validate a value change."""
        if not isinstance(value, torch.Tensor):
            self.error(objekt, name, value)
        return value


class Sequence(Tuple):
    def validate(self, objekt, name, value):
        if not isinstance(value, (str, bytes)) and isinstance(value, Sequence):
            value = list(value)
        newvalue = value
        inner_trait = self.inner_traits()[0]
        if not isinstance(value, list) or (
            isinstance(inner_trait.trait_type, traits.List)
            and not isinstance(inner_trait.trait_type, Sequence)
            and not isinstance(value[0], list)
        ):
            newvalue = [value]
        value = super().validate(objekt, name, newvalue)
        if value:
            return value
        self.error(objekt, name, value)


traits.Int = Int
traits.Float = Float
traits.Str = traits.Unicode
traits.Tuple = Tuple
traits.Tensor = Tensor
traits.Sequence = Sequence


TRAIT_TYPES = {
    "str": "traits.Str",
    "int": "traits.Int",
    "float": "traits.Float",
    "bool": "traits.Bool",
    "Tensor": "traits.Tensor",
    "list": "traits.List",
    "tuple": "traits.Tuple",
    "sequence": "traits.Sequence",
    "array": "traits.Array",
    "union": "traits.Either",
}
