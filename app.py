"""
Streamlit UI for the MVNO financial sandbox.
Run locally with:   streamlit run app.py
Deploy on Streamlit Cloud or any container.
"""

import streamlit as st
import pandas as pd
import altair as alt

from finance_engine import run_model, load_defaults, __version__

st.set_page_config(page_title="MVNO Scenario Model", layout="wide")
defaults = load_defaults()

# ---------------------------------------------------------------- sidebar ---
st.sidebar.header("🔧 Assumptions")
with st.sidebar.form("scenario"):
    gross_adds_k = st.slider(
        "Organic gross adds (k / month)",
        1,
        100,
        int(defaults["gross_adds_k"]),
    )
    marketing_k = st.slider(
        "Paid marketing (€k / month)",
        0,
        5000,
        int(defaults["marketing_k"]),
        step=50,
    )
    arpu = st.number_input(
        "ARPU (€ / sub / month)",
        5.0,
        50.0,
        float(defaults["arpu"]),
        0.1,
    )
    churn_pct = st.slider(
        "Monthly churn (%)",
        0.0,
        10.0,
        float(defaults["churn_pct"]),
        0.1,
    )
    submitted = st.form_submit_button("Run scenario")

# ----------------------------------------------------------------- header ---
st.title("📈 Dutch MVNO Scenario Model")
st.caption(f"Model engine v{__version__}")

# ----------------------------------------------------------------- results ---
if submitted:
    df, kpi = run_model(
        gross_adds_k=gross_adds_k,
        marketing_k=marketing_k,
        arpu=arpu,
        churn_pct=churn_pct,
    )

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pay‑back (months)", kpi["payback_months"] or "‒")
    c2.metric("NPV – 5 yr @ 8 %", f"€{kpi['npv']/1e6:,.2f} M")
    c3.metric("Peak funding need", f"€{kpi['peak_cash_need']/1e6:,.2f} M")
    c4.metric("Subs at month 60", f"{kpi['sub_count_end']:,}")

    # Charts
    base_tab, cash_tab, table_tab = st.tabs(
        ["📊 Subscribers", "💶 Cash", "📜 Table"]
    )

    with base_tab:
        st.altair_chart(
            alt.Chart(df)
            .mark_line()
            .encode(x="Month:Q", y="Subscribers:Q")
            .properties(height=300),
            use_container_width=True,
        )

    with cash_tab:
        st.altair_chart(
            alt.Chart(df)
            .mark_area()
            .encode(x="Month:Q", y="CumCash:Q")
            .properties(height=300),
            use_container_width=True,
        )

    with table_tab:
        st.dataframe(
            df[
                [
                    "Month",
                    "Subscribers",
                    "Revenue",
                    "EBIT",
                    "Cash",
                    "CumCash",
                ]
            ].style.format({"Revenue": "€{:.0f}", "CumCash": "€{:.0f}"}),
            height=600,
        )

    # Download
    with st.expander("Download monthly table (Excel)"):
        buf = pd.ExcelWriter("projection.xlsx", engine="openpyxl")
        df.to_excel(buf, index=False, sheet_name="Projection")
        buf.close()
        with open("projection.xlsx", "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                file_name="mvno_projection.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
else:
    st.info("Use the controls in the sidebar to run a scenario.")
