
# --- Imports ---
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from common.data_queries import general_bigquery_query


# --- Chart/UI Helper Functions ---
def make_line_chart(df: pd.DataFrame, y_col: str, title: str, y_percent: bool = False) -> px.line:
    fig = px.line(
        df,
        x="dt",
        y=y_col,
        title=title,
        labels={y_col: y_col.replace("_", " ").title(), "PERIOD_YEAR_MONTH": "Period Year Month"},
        height=600,
    )
    fig.update_layout(yaxis_title=y_col.replace("_", " ").title(), xaxis_title="Period Year Month")
    if y_percent:
        fig.update_yaxes(tickformat=".0%")
    else:
        fig.update_yaxes(tickformat=",.0f")
    return fig

def plot_in_columns(figs: list, columns: list):
    for idx, fig in enumerate(figs):
        columns[idx % len(columns)].plotly_chart(fig, use_container_width=True)

# --- Helper Functions ---
def aggregate_geo(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    agg_dict = {
        "rev_recur_tn": "sum",
        "rev_non_recur_tn": "sum",
        "rev_recur_vula": "sum",
        "rev_non_recur_vula": "sum",
        "abo_antall_tn": "sum",
        "abo_antall_vula": "sum",
    }
    grp = df.groupby(group_cols).agg(agg_dict).reset_index()
    grp["arpu_per_abo_tn"] = np.where(
        grp["abo_antall_tn"] == 0,
        0,
        (grp["rev_recur_tn"] + grp["rev_non_recur_tn"]) / grp["abo_antall_tn"],
    )
    grp["arpu_per_abo_vula"] = np.where(
        grp["abo_antall_vula"] == 0,
        0,
        (grp["rev_recur_vula"] + grp["rev_non_recur_vula"]) / grp["abo_antall_vula"],
    )
    grp["total_subs"] = grp["abo_antall_tn"] + grp["abo_antall_vula"]
    grp["vula_sub_share"] = np.where(
        grp["total_subs"] == 0,
        0,
        grp["abo_antall_vula"] / grp["total_subs"],
    )
    return grp

tn_arpu_query = """
SELECT
  gsa.billing_segment,
  gsa.stock_segment,
  gsa.PERIOD_YEAR_MONTH,
  COUNT(gsa.ABONNENT_NR) AS abo_antall,
  SUM(gsa.rev_recur) AS rev_recur,
  SUM(gsa.rev_non_recur) AS rev_non_recur,
  (SUM(gsa.rev_recur) + SUM(gsa.rev_non_recur))/COUNT(gsa.ABONNENT_NR) AS arpu_per_abo,
  gsa.COUNTY_ID,
  gsa.COUNTY,
  gsa.MUNICIPAL_ID,
  gsa.MUNICIPAL,
  gsa.POSTCODE_ID,
  gsa.POST_OFFICE
FROM
  `spectrum-analytics-secure.fiber_rev_no_test_mirror.geo_sub_arpu_terje_tempo` gsa
WHERE
  gsa.stock_segment = "CDK FIBER SDU"
GROUP BY
  ALL
"""
tn_rabatt_query = """
SELECT
  gsa.billing_segment,
  gsa.stock_segment,
  gsa.PERIOD_YEAR_MONTH,
  COUNT(gsa.ABONNENT_NR) AS abo_antall,
  SUM(gsa.rev_recur) AS rev_recur,
  SUM(gsa.rev_non_recur) AS rev_non_recur,
  (SUM(gsa.rev_recur) + SUM(gsa.rev_non_recur))/COUNT(gsa.ABONNENT_NR) AS arpu_per_abo,
  gsa.COUNTY_ID,
  gsa.COUNTY,
  gsa.MUNICIPAL_ID,
  gsa.MUNICIPAL,
  gsa.POSTCODE_ID,
  gsa.POST_OFFICE
FROM
  `spectrum-analytics-secure.fiber_rev_no_test_mirror.GEO_SUB_RABATT_TERJE_TEMPO` gsa
WHERE
  gsa.stock_segment = "CDK FIBER SDU"
GROUP BY
  ALL
"""

vula_arpu_qry = """

SELECT
  gsa.segment,
  gsa.project_segment,
  extract(YEAR from gsa.dt) as YEAR,
  extract(MONTH from gsa.dt) AS MONTH,
  SUM(gsa.num_subs) AS abo_antall,
  SUM(gsa.rev_recur) AS rev_recur,
  SUM(gsa.rev_non_recur) AS rev_non_recur,
  (SUM(gsa.rev_recur) + SUM(gsa.rev_non_recur))/SUM(gsa.num_subs) AS arpu_per_abo,
  gsa.COUNTY_ID,
  gsa.COUNTY,
  gsa.MUNICIPAL_ID,
  gsa.MUNICIPAL,
  gsa.POSTCODE_ID,
  gsa.POST_OFFICE
FROM
  `spectrum-analytics-secure.fiber_rev_no_test_mirror.geo_vula_sub_arpu_terje_tempo` AS gsa
  group by ALL
"""

def abo_query(year_month: int) -> str:
  return f"""
  WITH
    subs AS (
      SELECT
        b.ABONNENT_NR,
        b.PERIOD_YEAR_MONTH,
        s.billing_segment,
        pd.SOURCE_SYSTEM_NAME,
        pd.SOURCE_PRODUCT_ID_1,
        b.PRODUKT_NR,
        pd.PRODUCT_NAME,
        SUM(
          CASE
            WHEN INVOICE_TERM = "T" THEN AMOUNT
            ELSE 0
            END)
          - SUM(
            CASE
              WHEN INVOICE_TERM = "T" THEN DISCOUNT
              ELSE 0
              END) AS SUB_REVENUE_RECURRING_EXCL_MVA_TOTAL,
        SUM(
          CASE
            WHEN INVOICE_TERM = "E" THEN AMOUNT
            ELSE 0
            END)
          - SUM(
            CASE
              WHEN INVOICE_TERM = "E" THEN DISCOUNT
              ELSE 0
              END) AS SUB_REVENUE_NONRECURRING_EXCL_MVA_TOTAL
      FROM
        `spectrum-analytics-secure.fiber_rev_no_test_mirror.BILLING_PERIOD_FACT` b
      INNER JOIN
        `spectrum-analytics-secure.fiber_rev_no_test_mirror.VI_MAT_FIBER_SUBS` s
        ON
          b.ABONNENT_NR = s.ABONNENT_NR
          AND b.PERIOD_YEAR_MONTH = s.PERIOD_YEAR_MONTH
      LEFT JOIN
        `spectrum-analytics-secure.fiber_rev_no_test_mirror.PRODUCT_DIM` AS pd
        ON
          pd.SOURCE_PRODUCT_ID_1 = CAST(b.PRODUKT_NR AS string)
      WHERE
        pd.SOURCE_SYSTEM_NAME = "KAS"
        AND b.PERIOD_YEAR_MONTH = {year_month}
        AND s.billing_segment = "SDU"
      GROUP BY
        ALL
    ),
    subsc_type AS (
      SELECT DISTINCT
        bpf.ABONNENT_NR,
        bpf.PERIOD_YEAR_MONTH,
        pvt.PRODUCT_NAME,
        pvt.SOURCE_PRODUCT_ID_1
      FROM
        `spectrum-analytics-secure.fiber_rev_no_test_mirror.BILLING_PERIOD_FACT`
          AS bpf
      INNER JOIN
        `spectrum-analytics-secure.fiber_rev_no_test_mirror.PRODUCT_V_TMP` AS pvt
        ON CAST(bpf.PRODUKT_NR AS STRING) = pvt.SOURCE_PRODUCT_ID_1
      WHERE bpf.PERIOD_YEAR_MONTH = {year_month}
      and pvt.SOURCE_SYSTEM_NAME = "KAS"
      and pvt.TECHNOLOGY = "FIBER"
    ),
    tv_subsc AS (
      SELECT DISTINCT
        tv_bpf.ABONNENT_NR,
        tv_bpf.PERIOD_YEAR_MONTH,
        tv_pvt.PRODUCT_NAME,
      FROM
        `spectrum-analytics-secure.fiber_rev_no_test_mirror.BILLING_PERIOD_FACT`
          AS tv_bpf
      INNER JOIN
        `spectrum-analytics-secure.fiber_rev_no_test_mirror.PRODUCT_V_TMP`
          AS tv_pvt
        ON CAST(tv_bpf.PRODUKT_NR AS STRING) = tv_pvt.SOURCE_PRODUCT_ID_1
      WHERE
        tv_pvt.PRODUCT_NAME = "Grunnpakke TV"
        and tv_pvt.SOURCE_SYSTEM_NAME = "KAS"
        AND tv_bpf.PERIOD_YEAR_MONTH = {year_month}
    )
  SELECT
    subs.billing_segment segment,
    subs.SOURCE_SYSTEM_NAME,
    subs.PERIOD_YEAR_MONTH,
    subs.PRODUKT_NR,
    subs.PRODUCT_NAME AS invoice_line_name,
    subsc_type.SOURCE_PRODUCT_ID_1,
    subsc_type.PRODUCT_NAME AS subscription_type,
    Case when COALESCE(tv_subsc.PRODUCT_NAME, "NO") = "NO" then "NO" else "YES" end AS tv_subsc,
    COUNT(subs.ABONNENT_NR) AS units,
    Round(
      sum(SUB_REVENUE_RECURRING_EXCL_MVA_TOTAL)
        + sum(SUB_REVENUE_NONRECURRING_EXCL_MVA_TOTAL),
      0) AS tot_rev_nok_ex_vat,
    Round(
      1.25 * (
        sum(SUB_REVENUE_RECURRING_EXCL_MVA_TOTAL)
        + sum(SUB_REVENUE_NONRECURRING_EXCL_MVA_TOTAL)),
      0) AS tot_rev_nok_incl_vat,
  FROM subs
  LEFT JOIN subsc_type
    ON
      subsc_type.ABONNENT_NR = subs.ABONNENT_NR
      AND subsc_type.PERIOD_YEAR_MONTH = subs.PERIOD_YEAR_MONTH
  LEFT JOIN tv_subsc
    ON
      tv_subsc.ABONNENT_NR = subs.ABONNENT_NR
      AND tv_subsc.PERIOD_YEAR_MONTH = subs.PERIOD_YEAR_MONTH
  GROUP BY ALL
  ORDER BY
    sum(SUB_REVENUE_RECURRING_EXCL_MVA_TOTAL),
    subs.PERIOD_YEAR_MONTH,
    COUNT(subs.ABONNENT_NR) DESC,
    subs.PRODUCT_NAME
    """
rabatt_run = st.radio("Kjøring bare på rabatter?", ("Nei", "Ja"), index=0, key="tn_rabatter_included")

@st.cache_data(show_spinner=False)
def cached_query(qry: str) -> pd.DataFrame:
   return general_bigquery_query(qry)

tn_arpu_df_tmp = cached_query(tn_arpu_query)
tn_arpu_df_tmp = tn_arpu_df_tmp[tn_arpu_df_tmp["billing_segment"] == "SDU"]
tn_arpu_df_tmp = tn_arpu_df_tmp.drop(columns=["stock_segment"])

tn_rabatt_df = cached_query(tn_rabatt_query)
tn_rabatt_df = tn_rabatt_df[tn_rabatt_df["billing_segment"] == "SDU"]
tn_rabatt_df = tn_rabatt_df.drop(columns=["stock_segment"])

if rabatt_run == "Nei":
    tn_arpu_df = tn_arpu_df_tmp.copy()
else:
    rabatt_subs_only = st.radio("Kjøring kun med kunder med rabatt?", ("Nei", "Ja"), index=0, key="tn_rabatter_only")
    if rabatt_subs_only == "Ja":
      tn_arpu_df_tmp = tn_arpu_df_tmp.drop(columns=["rev_recur", "rev_non_recur", "arpu_per_abo", "abo_antall"])
      tn_rabatt_df = tn_rabatt_df.drop(columns=["arpu_per_abo"])
    else:
      tn_arpu_df_tmp = tn_arpu_df_tmp.drop(columns=["rev_recur", "rev_non_recur", "arpu_per_abo"])
      tn_rabatt_df = tn_rabatt_df.drop(columns=["arpu_per_abo", "abo_antall"])
    
    tn_arpu_df = tn_arpu_df_tmp.merge(tn_rabatt_df, how="left", on=["billing_segment", "PERIOD_YEAR_MONTH", "COUNTY_ID", "COUNTY", "MUNICIPAL_ID", "MUNICIPAL", "POSTCODE_ID", "POST_OFFICE"], suffixes=("_orig", "_rabatt")).fillna(0)
    tn_arpu_df["arpu_per_abo"] = (tn_arpu_df["rev_recur"]+tn_arpu_df["rev_non_recur"])/ tn_arpu_df["abo_antall"]

vula_arpu_df_tmp = cached_query(vula_arpu_qry)
vula_arpu_df_tmp = vula_arpu_df_tmp[vula_arpu_df_tmp["segment"] == "SDU"]
vula_arpu_df = vula_arpu_df_tmp.groupby(["YEAR", "MONTH", "COUNTY_ID", "COUNTY", "MUNICIPAL_ID", "MUNICIPAL",
"POSTCODE_ID", "POST_OFFICE", "segment", ]).agg({"abo_antall": "sum", "rev_recur": "sum", "rev_non_recur": "sum"}).reset_index()


# create new column PERIOD_YEAR_MONTH in vula_arpu_df (as integer) and remove year and month columns
vula_arpu_df["PERIOD_YEAR_MONTH"] = vula_arpu_df["YEAR"].astype(str) + vula_arpu_df["MONTH"].astype(str).str.zfill(2)
vula_arpu_df["PERIOD_YEAR_MONTH"] = vula_arpu_df["PERIOD_YEAR_MONTH"].astype(int)
vula_arpu_df = vula_arpu_df.drop(columns=["YEAR", "MONTH"])

tn_vula_arpu_df = tn_arpu_df.merge(vula_arpu_df, how="left", on=["PERIOD_YEAR_MONTH", "COUNTY_ID", "COUNTY", "MUNICIPAL_ID", "MUNICIPAL", "POSTCODE_ID", "POST_OFFICE"], suffixes=("_tn", "_vula")).fillna(0)

tn_vula_summary = tn_vula_arpu_df.groupby(["PERIOD_YEAR_MONTH"]).agg({"abo_antall_tn": "sum", "rev_recur_tn": "sum", "rev_non_recur_tn": "sum", "abo_antall_vula": "sum", "rev_recur_vula": "sum", "rev_non_recur_vula": "sum"}).reset_index()

st.title("Geographical TN and VULA ARPU and subs data")
#plot dataframe inside expander
with st.expander("TN and VULA ARPU and subs data", expanded=False):
  st.dataframe(tn_vula_arpu_df)

county_grp = aggregate_geo(tn_vula_arpu_df, ["COUNTY_ID", "COUNTY", "PERIOD_YEAR_MONTH"])
county_grp = county_grp.sort_values(by=["COUNTY_ID", "PERIOD_YEAR_MONTH"])
county_grp["dt"] = pd.to_datetime(county_grp["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")

municipal_grp = aggregate_geo(tn_vula_arpu_df, ["MUNICIPAL_ID", "MUNICIPAL", "COUNTY_ID", "COUNTY", "PERIOD_YEAR_MONTH"])
municipal_grp = municipal_grp.sort_values(by=["MUNICIPAL_ID", "PERIOD_YEAR_MONTH"])
municipal_grp["dt"] = pd.to_datetime(municipal_grp["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")

postcode_grp = aggregate_geo(tn_vula_arpu_df, ["POSTCODE_ID", "POST_OFFICE", "MUNICIPAL_ID", "MUNICIPAL", "COUNTY_ID", "COUNTY", "PERIOD_YEAR_MONTH"])
postcode_grp = postcode_grp.sort_values(by=["POSTCODE_ID", "PERIOD_YEAR_MONTH"])
postcode_grp["dt"] = pd.to_datetime(postcode_grp["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")

# CREATE drop down to select between county, municipal and postcode level
col_a, col_b = st.columns(2)
with col_a:
  level = st.selectbox("Select level", ["County", "Municipal", "Postcode"], index=0)
  county_list = list(county_grp["COUNTY"].unique())
  county_list = sorted(county_list)
  municipal_list = list(municipal_grp["MUNICIPAL"].unique())
  municipal_list = sorted(municipal_list)
  match level:
      case "County":
          filtered_df = county_grp.copy()
          legend = "COUNTY"
      case "Municipal":
          filtered_county = st.selectbox("Select county", county_list, index=0, key="municipal_county")
          selected_subitem = filtered_county
          filtered_df = municipal_grp.copy()
          filtered_df = filtered_df[filtered_df["COUNTY"] == filtered_county]
          legend = "MUNICIPAL"
      case "Postcode":
          filtered_municipal = st.selectbox("Select municipal", municipal_list, index=0, key="postcode_municipal")
          selected_subitem = filtered_municipal
          filtered_df = postcode_grp.copy()
          filtered_df = filtered_df[filtered_df["MUNICIPAL"] == filtered_municipal]
          filtered_df["ID_OFFICE"] = filtered_df["POSTCODE_ID"].astype(str) + " - " + filtered_df["POST_OFFICE"]
          legend = "ID_OFFICE"
      case _:
          filtered_df = county_grp.copy()
with col_b:
    (arpu_min, arpu_max) = st.slider(
        "Select ARPU range to display",
        min_value=0 if rabatt_run == "Nei" else -2000,
        max_value=2000,
        value=(1, 2000 if level == "County" else 700) if rabatt_run == "Nei" else (-2000, 2000),
        step=50,
    )
    month_year_filter = st.selectbox("Select month/year", options=list(filtered_df["PERIOD_YEAR_MONTH"].sort_values(ascending=False).unique()), index=0)
    first_year_month_plot = st.selectbox("Select first year/month to plot from", options=list(filtered_df["PERIOD_YEAR_MONTH"].sort_values(ascending=False).unique()), index=24)
    if first_year_month_plot >= month_year_filter:
        st.warning("First year/month to plot from must be earlier than month/year filter. Resetting to earliest available.")
        st.stop()

filtered_df = filtered_df[filtered_df["PERIOD_YEAR_MONTH"] >= first_year_month_plot]

# break line of code below
tab_summary, tab_geo_type, tab_arpu_ranked, tab_invoice_line_data, time_dev = st.tabs(
    ["Summary", "Geographical trends", "Ranked ARPU", "Invoice line data", "Development over time"]
)

with tab_summary:
  st.header(f"Summary: {'Norway' if level == 'County' else selected_subitem}")
  summary_df = filtered_df.copy()
  summary_df_grp = summary_df.groupby(["PERIOD_YEAR_MONTH"]).agg(
     {"abo_antall_tn": "sum", "rev_recur_tn": "sum", "rev_non_recur_tn": "sum", "abo_antall_vula": "sum",
       "rev_recur_vula": "sum", "rev_non_recur_vula": "sum"}).reset_index()
  summary_df_grp["total_subs"] = summary_df_grp["abo_antall_tn"] + summary_df_grp["abo_antall_vula"]
  summary_df_grp["arpu_per_abo_tn"] = np.where(
    summary_df_grp["abo_antall_tn"] == 0,
    0,
    (summary_df_grp["rev_recur_tn"] + summary_df_grp["rev_non_recur_tn"]) / summary_df_grp["abo_antall_tn"]
  )
  summary_df_grp["arpu_per_abo_vula"] = np.where(
    summary_df_grp["abo_antall_vula"] == 0,
    0,
    (summary_df_grp["rev_recur_vula"] + summary_df_grp["rev_non_recur_vula"]) / summary_df_grp["abo_antall_vula"]
  )
  summary_df_grp["vula_sub_share"] = np.where(
    summary_df_grp["total_subs"] == 0,
    0,
    summary_df_grp["abo_antall_vula"] / summary_df_grp["total_subs"]
  )
  summary_df_grp["dt"] = pd.to_datetime(summary_df_grp["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")

  chart_list = [
      ("abo_antall_tn", False),
      ("abo_antall_vula", False),
      ("total_subs", False),
      ("vula_sub_share", True),
      ("arpu_per_abo_tn", False),
      ("arpu_per_abo_vula", False)
  ]
  cols = st.columns(3)
  figs = [make_line_chart(summary_df_grp, p, f"{p} over time", y_percent=percent) for p, percent in chart_list]
  plot_in_columns(figs, cols)
  with st.expander("See data used in plots", expanded=False):
    st.dataframe(summary_df_grp.style.format(subset=summary_df_grp.columns[1:-1], formatter="{:,.0f}").format(subset=["vula_sub_share"], formatter="{:.1%}"), use_container_width=True)
with tab_geo_type:
  st.header("Geographical ARPU and subscriber trends")
  col_11, col_12 = st.columns(2)
  with col_11:
    fig = px.line(filtered_df, x="dt", y=["arpu_per_abo_tn"], color=legend, markers=True, title=f"ARPU TN - {level} level", labels={"value": "ARPU", "dt": "Date", "variable": "Type"}, height=1000)
    fig.update_layout(yaxis_title="ARPU", xaxis_title="Date", legend_title=legend)
    st.plotly_chart(fig, use_container_width=True, height=1000)
  with col_12:
    fig2 = px.line(filtered_df, x="dt", y=["arpu_per_abo_vula"], color=legend, markers=True, title=f"ARPU VULA - {level} level", labels={"value": "ARPU", "dt": "Date", "variable": "Type"}, height=1000)
    fig2.update_layout(yaxis_title="ARPU", xaxis_title="Date", legend_title=legend)
    st.plotly_chart(fig2, use_container_width=True)
  with col_11:
    fig3 = px.line(filtered_df, x="dt", y=["abo_antall_tn"], color=legend, markers=True, title=f"Number of TN subs - {level} level", labels={"value": "Number of subs", "dt": "Date", "variable": "Type"}, height=1000)
    fig3.update_layout(yaxis_title="Number of TN subs", xaxis_title="Date", legend_title=legend)
    st.plotly_chart(fig3, use_container_width=True)
  with col_12:
    fig4 = px.line(filtered_df, x="dt", y=["abo_antall_vula"], color=legend, markers=True, title=f"Number of VULA subs - {level} level", labels={"value": "Number of subs", "dt": "Date", "variable": "Type"}, height=1000)
    fig4.update_layout(yaxis_title="Number of VULA subs", xaxis_title="Date", legend_title=legend)
    st.plotly_chart(fig4, use_container_width=True)
# add chart with vula subs share
  with col_11:
    fig5 = px.line(filtered_df, x="dt", y=["vula_sub_share"], color=legend, markers=True, title=f"VULA subs share of total subs - {level} level", labels={"value": "VULA subs share", "dt": "Date", "variable": "Type"}, height=1000)
    fig5.update_layout(yaxis_title="VULA subs share", xaxis_title="Date", legend_title=legend)
    fig5.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig5, use_container_width=True)
  with st.expander("See data used in plots", expanded=False):
    st.dataframe(filtered_df)


def plot_ranked_arpu_and_subs(grouped_df: pd.DataFrame, level: str) -> None:
  match level:
        case "County":
            index_list = ["COUNTY_ID", "COUNTY"]
        case "Municipal":
            index_list = ["MUNICIPAL_ID", "MUNICIPAL", "COUNTY"]
        case "Postcode":
            index_list = ["POSTCODE_ID", "POST_OFFICE", "MUNICIPAL"]
  filtered_df = grouped_df.copy()
  filtered_df = filtered_df[filtered_df["PERIOD_YEAR_MONTH"] >= first_year_month_plot]
  if filtered_df.empty:
        st.warning("No data available for the selected first year/month to plot from.")
  filtered_arpu_pivot = filtered_df.pivot_table(
    index=index_list,
    columns=["PERIOD_YEAR_MONTH"],
    values="arpu_per_abo_tn",
    aggfunc="sum",
    fill_value=0,
  ).reset_index()
  # order pivot based on arpu in selected Period_YEAR_MONTH
  filtered_arpu_pivot = filtered_arpu_pivot[
    filtered_arpu_pivot[month_year_filter].between(arpu_min, arpu_max)
  ]
  filtered_arpu_pivot = filtered_arpu_pivot.sort_values(by=month_year_filter, ascending=True)
  filter_tn_subs_pivot = filtered_df.pivot_table(
    index=index_list,
    columns=["PERIOD_YEAR_MONTH"],
    values="abo_antall_tn",
    aggfunc="sum",
    fill_value=0,
  ).reset_index()
  # sort filter_tn_subs_pivot based on index in filtered_arpu_pivot
  filter_tn_subs_pivot = filter_tn_subs_pivot.set_index(index_list).reindex(
    filtered_arpu_pivot.set_index(index_list).index
  ).reset_index()
  filter_vula_subs_pivot = filtered_df.pivot_table(
    index=index_list,
    columns=["PERIOD_YEAR_MONTH"],
    values="abo_antall_vula",
    aggfunc="sum",
    fill_value=0,
  ).reset_index()
  filter_vula_subs_pivot = filter_vula_subs_pivot.set_index(index_list).reindex(
    filtered_arpu_pivot.set_index(index_list).index
  ).reset_index()
  filter_vula_sub_share_pivot = filtered_df.pivot_table(
    index=index_list,
    columns=["PERIOD_YEAR_MONTH"],
    values="vula_sub_share",
    aggfunc="sum",
    fill_value=0,
  ).reset_index()
  filter_vula_sub_share_pivot = filter_vula_sub_share_pivot.set_index(index_list).reindex(
    filtered_arpu_pivot.set_index(index_list).index
  ).reset_index()

  height = 35 * (len(filtered_arpu_pivot) + 1)
  st.header("ARPU TN")
  st.dataframe(filtered_arpu_pivot.style.format(subset=filtered_arpu_pivot.columns[3:], formatter="{:.0f}"), use_container_width=True, height=height)
  st.header("Number of TN subs")
  st.dataframe(filter_tn_subs_pivot.style.format(subset=filter_tn_subs_pivot.columns[3:], formatter="{:,.0f}"), use_container_width=True, height=height)
  st.header("Number of VULA subs")
  st.dataframe(filter_vula_subs_pivot.style.format(subset=filter_vula_subs_pivot.columns[3:], formatter="{:,.0f}"), use_container_width=True, height=height)
  st.header("VULA subs share of total subs")
  st.dataframe(filter_vula_sub_share_pivot.style.format(subset=filter_vula_sub_share_pivot.columns[3:], formatter="{:.1%}"), use_container_width=True, height=height)

with tab_arpu_ranked:
  st.header("ARPU and subscribes (Telenor retail and Vula) - ranked based on selected month/year and ARPU range")
  match level:
      case "County":
          plot_ranked_arpu_and_subs(county_grp.copy(), level="County")
      case "Municipal":
          plot_ranked_arpu_and_subs(municipal_grp.copy(), level="Municipal")
      case "Postcode":
        plot_ranked_arpu_and_subs(postcode_grp.copy(), level="Postcode")
      case _:
          st.warning("Please select a level to display ranked ARPU.")
with tab_invoice_line_data:
  st.header("Based on all  'fakturalinjer' for selected month/year")
  invoice_year_month = st.selectbox("Select invoice year month", options=list(tn_vula_arpu_df["PERIOD_YEAR_MONTH"].sort_values(ascending=False).unique()), index=0, key="invoice_line_year_month")
  invoice_line_df = cached_query(abo_query(invoice_year_month))
  sub_options = list(invoice_line_df["subscription_type"].unique())
  sub_options_filtered = [x for x in sub_options if x not in ["Grunnpakke TV", "Digital Grunnpakke B2B"]]
  subscriptions_drop_down = st.multiselect("Filter on subscription types", options=sub_options, default=sub_options_filtered, key="invoice_line_subscription_type") 
  invoice_line_df = invoice_line_df[invoice_line_df["subscription_type"].isin(subscriptions_drop_down)]
  sub_total = 0
  for i in subscriptions_drop_down:
    add_subs = invoice_line_df[(invoice_line_df["subscription_type"] == i) & (invoice_line_df["invoice_line_name"] == i)]["units"].sum()
    sub_total += add_subs
  st.write(f"Total subscriptions for selected subscription types: {sub_total:,}")
  invoice_line_grp = invoice_line_df.groupby(["invoice_line_name"]).agg({"units": "sum", "tot_rev_nok_ex_vat": "sum"}).reset_index()
  selected_total_subs = invoice_line_grp[invoice_line_grp["invoice_line_name"].isin(subscriptions_drop_down)]["units"].sum()
  total_row = pd.DataFrame({"invoice_line_name": ["Total net revenues"], "units": [sub_total], "tot_rev_nok_ex_vat": [invoice_line_grp["tot_rev_nok_ex_vat"].sum()]}, index=["Total"])
  invoice_line_grp = pd.concat([invoice_line_grp, total_row])
  # new column NOK_per_sub_ex_vat
  invoice_line_grp["NOK_per_unit_ex_vat"] = invoice_line_grp["tot_rev_nok_ex_vat"] / invoice_line_grp["units"]
  invoice_line_grp["NOK_per_avg_sub_ex_vat"] = invoice_line_grp["tot_rev_nok_ex_vat"] / sub_total
  invoice_line_grp = invoice_line_grp.sort_values(by="tot_rev_nok_ex_vat", ascending=False)
  
  
  with st.expander(f"Raw data. {invoice_year_month}: For all combinations of products and subscriptions", expanded=False):
    st.dataframe(invoice_line_df)
  
  def subsription_presenter(subscription_type: str, _df: pd.DataFrame) -> str:
      df_tmp = _df[_df["subscription_type"] == subscription_type]
      plot_df = pd.DataFrame(columns=["Total_revenues_ex_vat", "Total_subscriptions", "NOK_per_sub_ex_vat"])
      if df_tmp.empty:
          return "No data"
      total_subs = df_tmp[df_tmp["invoice_line_name"]==subscription_type]["units"].sum()
      tv_subs = df_tmp[df_tmp["invoice_line_name"].isin(["Grunnpakke TV"])]["units"].sum()
      tv_rev = df_tmp[(df_tmp["invoice_line_name"].str.contains("tv", case=False, na=False)) & (df_tmp["tot_rev_nok_ex_vat"]>0)]["tot_rev_nok_ex_vat"].sum()
      net_total = df_tmp["tot_rev_nok_ex_vat"].sum()
      sum_neg_items= df_tmp[df_tmp["tot_rev_nok_ex_vat"] < 0]["tot_rev_nok_ex_vat"].sum()
      sum_pos_items= df_tmp[df_tmp["tot_rev_nok_ex_vat"] > 0]["tot_rev_nok_ex_vat"].sum()
      headline_subscription = df_tmp[df_tmp["invoice_line_name"]==subscription_type]["tot_rev_nok_ex_vat"].sum()
      bb_tv_rabatt = df_tmp[df_tmp["invoice_line_name"]=="Bredbåndsrabatt med TV"]["tot_rev_nok_ex_vat"].sum()
      kabeltv_rabatt = df_tmp[df_tmp["invoice_line_name"]=="Rabatt Kabel-TV"]["tot_rev_nok_ex_vat"].sum()
      rabatt_lines = df_tmp[df_tmp["invoice_line_name"].str.contains("rabatt", case=False, na=False)]["tot_rev_nok_ex_vat"].sum()
      rabatt_ex_tv = rabatt_lines - bb_tv_rabatt - kabeltv_rabatt
      neg_rabatt_adjusted = sum_neg_items-rabatt_lines
      pos_headline_adjusted = sum_pos_items - headline_subscription- tv_rev
     
      plot_df.loc["Total net revenues", "Total_revenues_ex_vat"] = net_total
      plot_df.loc["Headline price", "Total_revenues_ex_vat"] = headline_subscription
      plot_df.loc["TV revenues", "Total_revenues_ex_vat"] = tv_rev
      plot_df.loc["Other revenues", "Total_revenues_ex_vat"] = pos_headline_adjusted
      plot_df.loc["Rabatt-GrunnpakkeTV", "Total_revenues_ex_vat"] = bb_tv_rabatt
      plot_df.loc["Rabatt-KabelTV", "Total_revenues_ex_vat"] = kabeltv_rabatt
      plot_df.loc["Andre Rabatter", "Total_revenues_ex_vat"] = rabatt_ex_tv
      plot_df.loc["Other negative items", "Total_revenues_ex_vat"] = neg_rabatt_adjusted
      plot_df.loc[:, "Total_subscriptions"] = total_subs
      plot_df.loc[:, "NOK_per_sub_ex_vat"] = plot_df["Total_revenues_ex_vat"] / total_subs
      st.subheader(f"{subscription_type}")
      #thousand separator for total_subs and tv_subs

      st.write(f"Total subscriptions: {total_subs:,}. TV subs: {tv_subs:,}. TV share of total subs: {tv_subs/total_subs:.1%}" )
      st.dataframe(plot_df.style.format(subset=plot_df.columns, formatter="{:,.0f}"), use_container_width=True)
      return subscription_type
  with st.expander("Subscription type details", expanded=False):
    col_1, col_2, col_3 = st.columns(3)
    for i in subscriptions_drop_down:
      if i == "Grunnpakke TV":
        pass
      else:
        for tv in ["YES", "NO", "YES&NO"]:
            if tv == "YES&NO":
              with col_3:
                with st.expander("With and without TV.", expanded=True):
                  df_tv_filter = invoice_line_df.copy()
                  subsription_presenter(i, df_tv_filter)
            else:
              if tv == "YES":
                with col_1:
                  with st.expander("Subscriptions with TV.", expanded=True):
                    df_tv_filter = invoice_line_df[invoice_line_df["tv_subsc"] == tv]
                    subsription_presenter(i, df_tv_filter)
              else:
                with col_2:
                  with st.expander("Subscriptions without TV.", expanded=True):
                    df_tv_filter = invoice_line_df[invoice_line_df["tv_subsc"] == tv]
                    subsription_presenter(i, df_tv_filter)

            
  # adjust height so that all rows are visible
  
  with st.expander("Invoice line data summary accross all subscription types", expanded=False):
    st.dataframe(invoice_line_grp.reset_index(drop=True).style.format(subset=invoice_line_grp.columns[1:], formatter="{:,.0f}"), use_container_width=True,height=35+35*len(invoice_line_grp))

  with st.expander("Time development", expanded=False):
    #create line charts for development over time (for every month and year since 2022) for count of Grunnpakke TV subscriptions and total subscriptions
    # line chart for total subscriptions over time
    st.header("Development of total subscriptions and Grunnpakke TV subscriptions over time")
    total_subs_list = []
    tv_subs_list = []
    tilknytninger_list = []
    tilknytning_rev_list = []
    for yr in range(2022, int(pd.Timestamp.now().strftime("%Y")) + 1):
        for m in range(1, 13):
            ym = yr * 100 + m
            if ym > int(pd.Timestamp.now().strftime("%Y%m")):
                continue
            invoice_line_df_tmp = cached_query(abo_query(ym))
            if invoice_line_df_tmp.empty:
                continue
            else:
              invoice_line_df_tmp = invoice_line_df_tmp[invoice_line_df_tmp["subscription_type"].isin(subscriptions_drop_down)]
              total_subs = invoice_line_df_tmp[invoice_line_df_tmp["invoice_line_name"].isin(subscriptions_drop_down)]["units"].sum()
              tv_subs = invoice_line_df_tmp[invoice_line_df_tmp["invoice_line_name"] == "Grunnpakke TV"]["units"].sum()
              tilknytninger = invoice_line_df_tmp[(invoice_line_df_tmp["invoice_line_name"].str.contains("tilknytning", case=False, na=False)) & (invoice_line_df_tmp["tot_rev_nok_ex_vat"]>0)]["units"].sum()
              tilknytning_rev = invoice_line_df_tmp[(invoice_line_df_tmp["invoice_line_name"].str.contains("tilknytning", case=False, na=False)) & (invoice_line_df_tmp["tot_rev_nok_ex_vat"]>0)]["tot_rev_nok_ex_vat"].sum()
              total_subs_list.append({"PERIOD_YEAR_MONTH": ym, "total_subs": total_subs})
              tv_subs_list.append({"PERIOD_YEAR_MONTH": ym, "tv_subs": tv_subs})
              tilknytninger_list.append({"PERIOD_YEAR_MONTH": ym, "tilknytninger": tilknytninger})
              tilknytning_rev_list.append({"PERIOD_YEAR_MONTH": ym, "tilknytning_rev": tilknytning_rev})

    total_subs_df = pd.DataFrame(total_subs_list)
    tv_subs_df = pd.DataFrame(tv_subs_list)
    tv_share_df = total_subs_df.merge(tv_subs_df, how="left", on=["PERIOD_YEAR_MONTH"]).fillna(0)
    tv_share_df["tv_subs_share"] = tv_share_df["tv_subs"] / tv_share_df["total_subs"]
    tilknytninger_df = pd.DataFrame(tilknytninger_list)
    tilknytning_rev_df = pd.DataFrame(tilknytning_rev_list)
    # create datetime column from PERIOD_YEAR_MONTH
    tv_share_df["dt"] = pd.to_datetime(tv_share_df["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")
    total_subs_df["dt"] = pd.to_datetime(total_subs_df["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")
    tv_subs_df["dt"] = pd.to_datetime(tv_subs_df["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")
    tilknytninger_df["dt"] = pd.to_datetime(tilknytninger_df["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")
    tilknytning_rev_df["dt"] = pd.to_datetime(tilknytning_rev_df["PERIOD_YEAR_MONTH"].astype(str), format="%Y%m")
    rev_per_tilknytning_df = tilknytning_rev_df.merge(tilknytninger_df, how="left", on=["PERIOD_YEAR_MONTH", "dt"]).fillna(0)
    rev_per_tilknytning_df["rev_per_tilknytning"] = np.where(
      rev_per_tilknytning_df["tilknytninger"] == 0,
      0,
      rev_per_tilknytning_df["tilknytning_rev"] / rev_per_tilknytning_df["tilknytninger"]
    )
    col_21, col_22= st.columns(2)
    with col_21:
        fig_total_subs = px.line(total_subs_df, x="dt", y="total_subs", markers=True, title="Total subscriptions over time", labels={"total_subs": "Total subscriptions", "dt": "Date"})
        fig_total_subs.update_layout(yaxis_title="Total subscriptions", xaxis_title="Date")
        st.plotly_chart(fig_total_subs, use_container_width=True)
    with col_22:
        fig_tv_subs = px.line(tv_subs_df, x="dt", y="tv_subs", markers=True, title="Grunnpakke TV subscriptions over time", labels={"tv_subs": "Grunnpakke TV subscriptions", "dt": "Date"})
        fig_tv_subs.update_layout(yaxis_title="Grunnpakke TV subscriptions", xaxis_title="Date")
        st.plotly_chart(fig_tv_subs, use_container_width=True)
    with col_21:
        fig_tv_share = px.line(tv_share_df, x="dt", y="tv_subs_share", markers=True, title="Share of Grunnpakke TV subscriptions over time", labels={"tv_subs_share": "Share of Grunnpakke TV subscriptions", "dt": "Date"})
        fig_tv_share.update_layout(yaxis_title="Share of Grunnpakke TV subscriptions", xaxis_title="Date")
        fig_tv_share.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig_tv_share, use_container_width=True)
    col_31, col_32= st.columns(2)
    with col_31:
        fig_tilknytninger = px.line(tilknytninger_df, x="dt", y="tilknytninger", markers=True, title="Units of  'tilknytning' in invoice name & positive revenue. Development over time", labels={"tilknytninger": "Tilknytninger", "dt": "Date"})
        fig_tilknytninger.update_layout(yaxis_title="Tilknytninger", xaxis_title="Date")
        st.plotly_chart(fig_tilknytninger, use_container_width=True)
    with col_32:
        fig_rev_per_tilknytning = px.line(rev_per_tilknytning_df, x="dt", y="rev_per_tilknytning", markers=True, title="Revenue per 'tilknytning'. Development over time", labels={"rev_per_tilknytning": "Revenue per tilknytning", "dt": "Date"})
        fig_rev_per_tilknytning.update_layout(yaxis_title="Revenue per tilknytning", xaxis_title="Date")
        st.plotly_chart(fig_rev_per_tilknytning, use_container_width=True)
