#!/usr/bin/env python3
"""
Listing (shap): SHAP feature attribution of the fitted classifier.

Extracted verbatim from the source-code listing (lst:shap) of the
manuscript "Soil amplification and collapse screening in Istanbul".
This is the code as documented in the paper; the structural/site
listings (siteresp, mdof, modal) are the representative reference
implementations described there. Verify paths and parameters against
your local environment before running.

Description (from the listing caption):
SHAP-based feature attribution applied to the fitted resist/collapse classifier, yielding the global ranking of site and structural predictors reported in Section (see manuscript).
"""

import shap
import numpy as np

# `model` is the fitted Random Forest / XGBoost classifier from Listing (lst:ml);
# `X` holds the feature names, `Xte` the standardised test-set features.
explainer  = shap.TreeExplainer(model)          # exact SHAP for tree ensembles
shap_vals  = explainer.shap_values(Xte)         # per-sample feature attributions

# Global importance: mean absolute SHAP value per feature
importance = np.abs(shap_vals).mean(axis=0)
ranking = sorted(zip(X.columns, importance), key=lambda t: t[1], reverse=True)
for name, val in ranking:
    print(f"{name:14s}  mean|SHAP| = {val:.3f}")

# Visual diagnostics for the dominant site-response predictors
shap.summary_plot(shap_vals, Xte, feature_names=X.columns, show=False)
shap.dependence_plot("vs30", shap_vals, Xte, feature_names=X.columns, show=False)
