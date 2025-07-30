################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
"""
Custom Converters for exportables.py

This module registers converters to transform the components in exportables.py into ONNX format.
It includes custom converters, shape calculators, and parsers to ensure compatibility
with ONNX export requirements.

Note:
Any converter with the `activate/use` flag won't work with arrays containing mixed types,
as ONNX can only define a single type for an output. As a result, every output will be cast
to the common type.
"""

from skl2onnx.common.data_types import StringTensorType, BooleanTensorType
from skl2onnx.common._topology import Operator

non_numeric_types = (StringTensorType, BooleanTensorType)


def is_all_non_numeric(operator_list: Operator.OperatorList):
    return all(type(inpt.type) in non_numeric_types for inpt in operator_list)


def is_all_numeric(operator_list: Operator.OperatorList):
    return all(type(inpt.type) not in non_numeric_types for inpt in operator_list)
