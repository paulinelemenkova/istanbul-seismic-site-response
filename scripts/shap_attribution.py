#!/usr/bin/env python3

import shap
import numpy as np

explainer  = shap.TreeExplainer(model)
shap_vals  = explainer.shap_values(Xte)

importance = np.abs(shap_vals).mean(axis=0)
ranking = sorted(zip(X.columns, importance), key=lambda t: t[1], reverse=True)
for name, val in ranking:
    print(f"{name:14s}  mean|SHAP| = {val:.3f}")

shap.summary_plot(shap_vals, Xte, feature_names=X.columns, show=False)
shap.dependence_plot("vs30", shap_vals, Xte, feature_names=X.columns, show=False)
