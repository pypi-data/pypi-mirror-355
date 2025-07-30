# survival_stats.py

from lifelines.statistics import logrank_test, multivariate_logrank_test
from lifelines import CoxPHFitter
import pandas as pd

def compute_survival_stats(time, event, group):
    df = pd.DataFrame({
        "time": time,
        "event": event,
        "group": group
    })

    results = {}
    unique_groups = df["group"].unique()
    if len(unique_groups) == 2:
        g1 = df[df["group"] == unique_groups[0]]
        g2 = df[df["group"] == unique_groups[1]]
        lr_result = logrank_test(g1["time"], g2["time"], g1["event"], g2["event"])
        results["logrank_p"] = lr_result.p_value
    else:
        lr_result = multivariate_logrank_test(time, group, event)
        results["logrank_p"] = lr_result.p_value

    try:
        cph = CoxPHFitter()
        df_encoded = pd.get_dummies(df, columns=["group"], drop_first=True)
        cph.fit(df_encoded, duration_col="time", event_col="event")
        summary = cph.summary
        results["hazard_ratio"] = summary["exp(coef)"].iloc[0]
        results["cox_p"] = summary["p"].iloc[0]
    except Exception:
        results["hazard_ratio"] = None
        results["cox_p"] = None

    return results
