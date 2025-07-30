################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
from onnxconverter_common import apply_identity
from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable

from autoai_libs.transformers.exportable import AllPassPreprocessingTransformer


def all_pass_preprocessing_shape_calculator(operator: Operator):
    pass


def all_pass_preprocessing_converter(scope: Scope, operator: Operator, container: ModelComponentContainer):
    for i, inpt in enumerate(operator.inputs):
        apply_identity(scope, [inpt.full_name], [operator.outputs[i].full_name], container)


def all_pass_preprocessing_parser(
    scope: Scope, model: AllPassPreprocessingTransformer, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)

    # inputs
    this_operator.inputs.extend(inputs)

    # outputs
    for i, inpt in enumerate(this_operator.inputs):
        this_operator.outputs.append(
            scope.declare_local_variable(f"OUT_{inpt.full_name}", type=inpt.type.__class__(shape=inpt.type.shape))
        )
    # ends
    return list(this_operator.outputs)


transformer = AllPassPreprocessingTransformer
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    all_pass_preprocessing_shape_calculator,
    all_pass_preprocessing_converter,
    parser=all_pass_preprocessing_parser,
)
