# app.py
import streamlit as st, pandas as pd, numpy as np, altair as alt

# ----------------------- parameters & defaults ----------------------------- #
DEFAULTS = dict(
    months=60,
    gross_adds_k=20,           # thousands
    marketing_k=200,           # €k
    arpu=15.0,                 # €
    churn_pct=2.0,             # %
    cac_eff=10.0,              # adds gained per 1k€ spent
    wholesale_fee=4.5,         # €/sub/month
    opex_k=150,                # €k fixed
    discount_rate=0.08,
)

def run_model(**kwargs):
    p = {**DEFAULTS, **kwargs}
    m = np.arange(p["months"])
    df = pd.DataFrame(index=m)
    df["Month"] = df.index + 1
    # paid acquisitions: linear response to marketing
    df["GrossAdds"] = p["gross_adds_k"] * 1e3 + p["marketing_k"] * p["cac_eff"]
    # churn probability
    df["ChurnRate"] = p["churn_pct"] / 100
    subs = []
    base = 0
    for r in df.itertuples():
        base += r.GrossAdds
        churned = base * r.ChurnRate
        base -= churned
        subs.append(base)
    df["Subscribers"] = subs
    df["Revenue"] = df["Subscribers"] * p["arpu"]
    df["Wholesale"] = df["Subscribers"] * p["wholesale_fee"]
    df["OPEX"] = p["opex_k"] * 1e3
    df["Marketing"] = p["marketing_k"] * 1e3
    df["Cash"] = df["Revenue"] - (df["Wholesale"] + df["OPEX"] + df["Marketing"])
    df["CumCash"] = df["Cash"].cumsum()
    # summary
    payback = int((df[df["CumCash"] > 0].index.min() or p["months"]) + 1)
    discount = (1 + p["discount_rate"]) ** (df.index / 12)
    npv = (df["Cash"] / discount).sum()
    peak_cash = df["CumCash"].min()
    summary = dict(payback_months=payback, npv=npv, peak_cash_need=-peak_cash)
    return df.reset_index(drop=True), summary

# ----------------------- Streamlit UI -------------------------------------- #
st.set_page_config("MVNO Scenario Model", layout="wide")
st.title("MVNO Financial Sandbox")

st.sidebar.header("Adjust Assumptions")
with st.sidebar.form("scenario"):
    gross_adds_k   = st.slider("Organic gross adds (k/month)", 1, 50, DEFAULTS["gross_adds_k"])
    marketing_k    = st.slider("Marketing spend (€k/month)", 0, 5000, DEFAULTS["marketing_k"])
    arpu           = st.number_input("ARPU (€)", 5.0, 50.0, DEFAULTS["arpu"], 0.5)
    churn_pct      = st.slider("Monthly churn (%)", 0.0, 10.0, DEFAULTS["churn_pct"], 0.1)
    run = st.form_submit_button("Run")
if run:
    df, s = run_model(gross_adds_k=gross_adds_k,
                      marketing_k=marketing_k,
                      arpu=arpu,
                      churn_pct=churn_pct)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Pay‑back (m)", s["payback_months"])
    kpi2.metric("5‑yr NPV (€M)", f"{s['npv']/1e6:,.1f}")
    kpi3.metric("Peak funding (€M)", f"{s['peak_cash_need']/1e6:,.1f}")
    st.line_chart(df.set_index("Month")[["Subscribers"]])
    st.altair_chart(
        alt.Chart(df).mark_area().encode(
            x="Month:Q", y="CumCash:Q", tooltip=["CumCash"]
        ).properties(height=250),
        use_container_width=True
    )
    with st.expander("Monthly details"):
        st.dataframe(df.head(36).style.format({"Revenue":"€{:.0f}", "CumCash":"€{:.0f}"}))
