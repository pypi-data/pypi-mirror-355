################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2019-2025. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import numpy as np
from sklearn import metrics as me
from sklearn.metrics import SCORERS, make_scorer, mean_squared_log_error, mean_squared_error

try:
    from autoai_common.sklearn.composite_scorer import CompositeScorer
except:
    pass


class CustomScorers:
    def __init__(self):
        # Negative RMSE
        fun = CustomScorers.root_mean_squared_error
        SCORERS["neg_root_mean_squared_error"] = make_scorer(fun, greater_is_better=False)
        me.__dict__["root_mean_squared_error"] = fun

        # Negative RMSLE
        fun = CustomScorers.root_mean_squared_log_error
        SCORERS["neg_root_mean_squared_log_error"] = make_scorer(fun, greater_is_better=False)
        me.__dict__["root_mean_squared_log_error"] = fun

        # Normalized Gini Coef. (needed for porto-seguro-safe-driver-prediction)
        fun = CustomScorers.normalized_gini_coefficient
        SCORERS["normalized_gini_coefficient"] = make_scorer(fun, greater_is_better=True)
        me.__dict__["normalized_gini_coefficient"] = fun

        # Initially, create default instance of CompositeScorer with use_cache=False
        # The user can tailor the instance to suit through its reinit() method.
        try:
            SCORERS["CompositeScorer"] = CompositeScorer(use_cache=False)
        except:
            pass

    @staticmethod
    def root_mean_squared_log_error(y_true, y_pred, sample_weight=None, multioutput="uniform_average"):
        msle = mean_squared_log_error(y_true, y_pred, sample_weight=sample_weight, multioutput=multioutput)
        return msle**0.5

    @staticmethod
    def root_mean_squared_error(y_true, y_pred, sample_weight=None, multioutput="uniform_average"):
        mse = mean_squared_error(y_true, y_pred, sample_weight=sample_weight, multioutput=multioutput)
        return mse**0.5

    @staticmethod
    def gini(actual, pred):
        assert len(actual) == len(pred)
        all = np.asarray(np.c_[actual, pred, np.arange(len(actual))], dtype=float)
        all = all[np.lexsort((all[:, 2], -1 * all[:, 1]))]
        totalLosses = all[:, 0].sum()
        giniSum = all[:, 0].cumsum().sum() / totalLosses

        giniSum -= (len(actual) + 1) / 2
        return giniSum / len(actual)

    @staticmethod
    def normalized_gini_coefficient(a, p):
        g = CustomScorers.gini(a, p)
        selfg = CustomScorers.gini(a, a)
        ngc = g / selfg
        return ngc


customScorers = CustomScorers()
