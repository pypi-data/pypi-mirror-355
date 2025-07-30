################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
from onnxruntime_extensions import onnx_op, PyCustomOpDef

from autoai_libs.utils.exportable_utils import (
    compress_str_column,
    numpy_replace_values,
    numpy_floatstr2float,
    numpy_permute_array,
)


@onnx_op(
    op_type="RemoveWhitespaces",
    inputs=[PyCustomOpDef.dt_string, PyCustomOpDef.dt_string],
    outputs=[PyCustomOpDef.dt_string],
)
def op_remove_whitespaces(X, misslist):
    Y = X.copy()
    for j in range(X.shape[1]):
        Y[:, j] = compress_str_column(X[:, j], misslist, "string")
    return Y


@onnx_op(
    op_type="CompressToHash",
    inputs=[PyCustomOpDef.dt_string, PyCustomOpDef.dt_string],
    outputs=[PyCustomOpDef.dt_double],
)
def op_compress_to_hash(X, misslist):
    Y = np.empty(X.shape, np.float64)
    for j in range(X.shape[1]):
        Y[:, j] = compress_str_column(X[:, j], misslist, "hash")
    return Y


@onnx_op(
    op_type="ReplaceFloatValues",
    inputs=[PyCustomOpDef.dt_float, PyCustomOpDef.dt_float],
    outputs=[PyCustomOpDef.dt_float],
    attrs={"filling_values": PyCustomOpDef.dt_float, "invert_flag": PyCustomOpDef.dt_string},
)
def op_replace_missing_values_num(X, reference_values_list, **kwargs):
    invert_flag = bool(kwargs.get("invert_flag", False))
    filling_values = kwargs.get("filling_values", np.nan)
    return numpy_replace_values(
        X, filling_values=filling_values, reference_values_list=list(reference_values_list), invert_flag=invert_flag
    )


@onnx_op(
    op_type="FloatStr2Float",
    inputs=[PyCustomOpDef.dt_string, PyCustomOpDef.dt_string],
    outputs=[PyCustomOpDef.dt_float],
)
def op_floatstr2float(X, missing_values_reference_list):
    Y = np.empty(X.shape, np.float32)
    for j in range(X.shape[1]):
        Y[:, j] = numpy_floatstr2float(X[:, j], missing_values_reference_list)
    return Y


@onnx_op(
    op_type="PermuteNumericArrays",
    inputs=[PyCustomOpDef.dt_float, PyCustomOpDef.dt_int64],
    outputs=[PyCustomOpDef.dt_float],
    attrs={"axis": PyCustomOpDef.dt_int64},
)
def op_permute_array_num(X, permutation_indices, **kwargs):
    axis = kwargs.get("axis", 0)
    return numpy_permute_array(X, permutation_indices=list(permutation_indices), axis=axis)
