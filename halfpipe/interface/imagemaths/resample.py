# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
"""
from pathlib import Path

import numpy as np
import nibabel as nib

from nipype.interfaces.ants.resampling import ApplyTransformsInputSpec
from niworkflows.interfaces.fixes import FixHeaderApplyTransforms
from templateflow.api import get as get_template

from nipype.interfaces.base import traits, InputMultiObject, File, isdefined

from ...resource import get as getresource
from ...utils import nvol


class ResampleInputSpec(ApplyTransformsInputSpec):
    input_space = traits.Either("MNI152NLin6Asym", "MNI152NLin2009cAsym", mandatory=True)
    reference_space = traits.Either("MNI152NLin6Asym", "MNI152NLin2009cAsym", mandatory=True)
    reference_res = traits.Int(mandatory=False)
    lazy = traits.Bool(default=True, usedefault=True, desc="only resample if necessary")

    # make not mandatory as these inputs will be computed from other inputs
    reference_image = File(
        argstr="--reference-image %s",
        mandatory=False,
        desc="reference image space that you wish to warp INTO",
        exists=True,
    )
    transforms = InputMultiObject(
        traits.Either(File(exists=True), "identity"),
        argstr="%s",
        mandatory=False,
        desc="transform files: will be applied in reverse order. For "
        "example, the last specified transform will be applied first.",
    )


class Resample(FixHeaderApplyTransforms):
    input_spec = ResampleInputSpec

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        self.resample = False

        input_space = self.inputs.input_space
        reference_space = self.inputs.reference_space
        reference_res = self.inputs.reference_res if isdefined(self.inputs.reference_res) else None

        if not isdefined(self.inputs.reference_image):
            if reference_res is not None:
                self.inputs.reference_image = get_template(reference_space, resolution=reference_res, desc="brain", suffix="mask")

        input_image = nib.load(self.inputs.input_image)
        reference_image = nib.load(self.inputs.reference_image)
        input_matches_reference = input_image.shape[:3] == reference_image.shape[:3]
        input_matches_reference = input_matches_reference and np.allclose(
            input_image.affine, reference_image.affine, atol=1e-2, rtol=1e-2  # tolerance of 0.01 mm
        )

        self.inputs.dimension = 3

        input_image_nvol = nvol(input_image)
        if input_image_nvol > 0:
            self.inputs.input_image_type = 3  # time series

        transforms = ["identity"]
        if input_space != reference_space:
            xfm = getresource(f"tpl_{reference_space}_from_{input_space}_mode_image_xfm.h5")
            assert Path(xfm).is_file()
            transforms = [str(xfm)]

        self.inputs.transforms = transforms

        if not input_matches_reference or set(transforms) != set(["identity"]) or not self.inputs.lazy:
            self.resample = True
            runtime = super(Resample, self)._run_interface(runtime, correct_return_codes)

        return runtime

    def _list_outputs(self):
        if self.resample:
            return super(Resample, self)._list_outputs()
        else:
            outputs = self.output_spec().get()
            outputs["output_image"] = self.inputs.input_image
            return outputs
