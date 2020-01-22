# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np

from nipype.interfaces.base import (
    isdefined,
    traits,
    TraitedSpec,
    DynamicTraitedSpec
)
from nipype.interfaces.io import (
    add_traits,
    IOBase
)
from nipype.interfaces.utility.base import _ravel
from nipype.utils.filemanip import ensure_list


class LogicalAndInputSpec(DynamicTraitedSpec):
    pass


class LogicalAndOutputSpec(TraitedSpec):
    out = traits.Bool(desc="output")


class LogicalAnd(IOBase):
    """

    """

    input_spec = LogicalAndInputSpec
    output_spec = LogicalAndOutputSpec

    def __init__(self, numinputs=0, **inputs):
        super(Filter, self).__init__(**inputs)
        self._numinputs = numinputs
        if numinputs >= 1:
            input_names = ["in%d" % (i + 1) for i in range(numinputs)]
            add_traits(self.inputs, input_names, trait_type=traits.Bool)
        else:
            input_names = []

    def _list_outputs(self):
        outputs = self._outputs().get()
        out = []

        if self._numinputs < 1:
            return outputs

        def getval(idx):
            return getattr(self.inputs, "in%d" % (idx + 1))

        values = [
            getval(idx) for idx in range(self._numinputs)
            if isdefined(getval(idx))
        ]

        out = False

        if len(values) > 0:
            out = np.all(values)

        outputs["out"] = out
        return outputs


class FilterInputSpec(DynamicTraitedSpec):
    axis = traits.Enum(
        "vstack",
        "hstack",
        usedefault=True,
        desc="direction in which to merge, hstack requires" +
             "same number of elements in each input",
    )
    no_flatten = traits.Bool(
        False,
        usedefault=True,
        desc="append to outlist instead of extending in vstack mode",
    )
    ravel_inputs = traits.Bool(
        False, usedefault=True, desc="ravel inputs when no_flatten is False"
    )


class FilterOutputSpec(TraitedSpec):
    out = traits.List(desc="Merged output")


class Filter(IOBase):
    """Basic interface class to merge inputs into a single list

    """

    input_spec = FilterInputSpec
    output_spec = FilterOutputSpec

    def __init__(self, numinputs=0, **inputs):
        super(Filter, self).__init__(**inputs)
        self._numinputs = numinputs
        if numinputs >= 1:
            input_names = ["in%d" % (i + 1) for i in range(numinputs)]
            add_traits(self.inputs, input_names)
            isenabled_input_names = \
                ["is_enabled%d" % (i + 1) for i in range(numinputs)]
            add_traits(self.inputs, isenabled_input_names,
                       trait_type=traits.Bool)
        else:
            input_names = []

    def _list_outputs(self):
        outputs = self._outputs().get()
        out = []

        if self._numinputs < 1:
            return outputs

        def getval(idx):
            return getattr(self.inputs, "in%d" % (idx + 1))

        def getisenabled(idx):
            return getattr(self.inputs, "is_enabled%d" % (idx + 1))

        values = [
            getval(idx) for idx in range(self._numinputs)
            if isdefined(getval(idx)) and
            (not isdefined(getisenabled(idx)) or getisenabled(idx))
        ]

        if self.inputs.axis == "vstack":
            for value in values:
                if isinstance(value, list) and not self.inputs.no_flatten:
                    out.extend(_ravel(value)
                               if self.inputs.ravel_inputs else value)
                else:
                    out.append(value)
        else:
            lists = [ensure_list(val) for val in values]
            out = [[val[i] for val in lists] for i in range(len(lists[0]))]

        outputs["out"] = out
        return outputs
