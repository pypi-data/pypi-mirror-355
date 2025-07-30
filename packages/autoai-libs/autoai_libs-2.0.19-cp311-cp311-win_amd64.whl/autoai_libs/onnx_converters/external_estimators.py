################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import warnings

import packaging.version as pv
from lightgbm import LGBMClassifier, LGBMRegressor
from onnxmltools import __version__ as oml_version
from onnxmltools.convert.lightgbm.operator_converters.LightGbm import convert_lightgbm
from onnxmltools.convert.xgboost.operator_converters.XGBoost import convert_xgboost
from skl2onnx import update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.shape_calculator import (
    calculate_linear_classifier_output_shapes,
    calculate_linear_regressor_output_shapes,
)
from xgboost import XGBRegressor


def skl2onnx_convert_lightgbm(scope: Scope, operator: Operator, container: ModelComponentContainer):
    options = scope.get_options(operator.raw_operator)
    operator.split = options.get("split")
    if operator.split is not None and pv.Version(oml_version) < pv.Version("1.9.2"):
        warnings.warn(
            f"Option split was released in version 1.9.2 but {oml_version} is installed. It will be ignored.",
            stacklevel=0,
        )
    convert_lightgbm(scope, operator, container)


update_registered_converter(
    LGBMRegressor,
    "LightGbmLGBMRegressor",
    calculate_linear_regressor_output_shapes,
    skl2onnx_convert_lightgbm,
    options={"split": None},
)

update_registered_converter(
    LGBMClassifier,
    "LightGbmLGBMClassifier",
    calculate_linear_classifier_output_shapes,
    convert_lightgbm,
    options={"nocl": [True, False], "zipmap": [True, False, "columns"]},
)


update_registered_converter(
    XGBRegressor,
    "XGBoostXGBRegressor",
    calculate_linear_regressor_output_shapes,
    convert_xgboost,
)
