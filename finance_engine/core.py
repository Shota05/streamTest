"""
core.py
-------

Vectorised projection logic:
  - customer base evolution
  - revenues, direct & fixed costs
  - free‑cash, cumulative cash, payback, NPV, peak funding
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from .assumptions import load_defaults


def _project_subscribers(gross_adds: np.ndarray, churn_rate: float) -> np.ndarray:
    """Return month‑by‑month in‑force subscriber base."""
    base = 0.0
    out = []
    for adds in gross_adds:
        base += adds
        churned = base * churn_rate
        base -= churned
        out.append(base)
    return np.asarray(out)


def run_model(**overrides) -> tuple[pd.DataFrame, dict]:
    """
    Execute a scenario.

    Parameters
    ----------
    **overrides
        Any assumption you want to change from the YAML baseline.

    Returns
    -------
    df  : Monthly projection table (Pandas DataFrame)
    meta: Summary KPIs (dict)
    """
    p = {**load_defaults(), **overrides}

    m = np.arange(p["months"])
    df = pd.DataFrame(index=m)
    df["Month"] = df.index + 1

    # --- Acquisition funnel ---------------------------------------------------
    df["GrossAdds"] = (
        p["gross_adds_k"] * 1e3 + p["marketing_k"] * p["cac_eff"]
    )

    # --- Subscriber base & churn ---------------------------------------------
    df["Subscribers"] = _project_subscribers(
        df["GrossAdds"].values, churn_rate=p["churn_pct"] / 100
    )

    # --- P&L items ------------------------------------------------------------
    df["Revenue"] = df["Subscribers"] * p["arpu"]
    df["Wholesale"] = df["Subscribers"] * p["wholesale_fee"]
    df["OPEX"] = p["opex_k"] * 1e3
    df["Marketing"] = p["marketing_k"] * 1e3
    df["EBIT"] = df["Revenue"] - (
        df["Wholesale"] + df["OPEX"] + df["Marketing"]
    )
    df["Tax"] = np.maximum(df["EBIT"], 0) * p["tax_rate"]
    df["Cash"] = df["EBIT"] - df["Tax"]
    df["CumCash"] = df["Cash"].cumsum()

    # --- Valuation metrics ----------------------------------------------------
    payback_idx = df.index[df["CumCash"] > 0]
    payback = int(payback_idx.min() + 1) if len(payback_idx) else None

    discount = (1 + p["discount_rate"]) ** (df.index / 12)
    npv = (df["Cash"] / discount).sum()

    peak_cash_need = -df["CumCash"].min()

    summary = dict(
        payback_months=payback,
        npv=npv,
        peak_cash_need=peak_cash_need,
        sub_count_end=int(df["Subscribers"].iloc[-1]),
    )
    return df.reset_index(drop=True), summary
