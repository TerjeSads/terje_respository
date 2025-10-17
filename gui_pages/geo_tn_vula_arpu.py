
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

tn_arpu_df = general_bigquery_query(tn_arpu_query)
tn_arpu_df = tn_arpu_df[tn_arpu_df["billing_segment"] == "SDU"]
tn_arpu_df = tn_arpu_df.drop(columns=["stock_segment"])

vula_arpu_df_tmp = general_bigquery_query(vula_arpu_qry)
vula_arpu_df_tmp = vula_arpu_df_tmp[vula_arpu_df_tmp["segment"] == "SDU"]
vula_arpu_df = vula_arpu_df_tmp.groupby(["YEAR", "MONTH", "COUNTY_ID", "COUNTY", "MUNICIPAL_ID", "MUNICIPAL", 
"POSTCODE_ID", "POST_OFFICE", "segment", ]).agg({"abo_antall": "sum", "rev_recur": "sum", "rev_non_recur": "sum"}).reset_index()


# create new column PERIOD_YEAR_MONTH in vula_arpu_df (as integer) and remove year and month columns
vula_arpu_df["PERIOD_YEAR_MONTH"] = vula_arpu_df["YEAR"].astype(str) + vula_arpu_df["MONTH"].astype(str).str.zfill(2)
vula_arpu_df["PERIOD_YEAR_MONTH"] = vula_arpu_df["PERIOD_YEAR_MONTH"].astype(int)
vula_arpu_df = vula_arpu_df.drop(columns=["YEAR", "MONTH"])

tn_vula_arpu_df = tn_arpu_df.merge(vula_arpu_df, how='left', on=['PERIOD_YEAR_MONTH', 'COUNTY_ID', 'COUNTY', 'MUNICIPAL_ID', 'MUNICIPAL', 'POSTCODE_ID', 'POST_OFFICE'], suffixes=('_tn', '_vula')).fillna(0)

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
    (arpu_min, arpu_max) = st.slider("Select ARPU range to display", min_value=0, max_value=2000, value=(1, 2000 if level == "County" else 700), step=50)
    month_year_filter = st.selectbox("Select month/year", options=list(filtered_df["PERIOD_YEAR_MONTH"].sort_values(ascending=False).unique()), index=0)
    first_year_month_plot = st.selectbox("Select first year/month to plot from", options=list(filtered_df["PERIOD_YEAR_MONTH"].sort_values(ascending=False).unique()), index=18)
    if first_year_month_plot >= month_year_filter:
        st.warning("First year/month to plot from must be earlier than month/year filter. Resetting to earliest available.")
        st.stop()

tab_summary, tab_geo_type, tab_arpu_ranked = st.tabs(["Summary", "Geographical trends", "Ranked ARPU"])
with tab_summary:
  st.header(f"Summary: {'Norway' if level == 'County' else selected_subitem}")
  summary_df = filtered_df.copy()
  summary_df_grp = summary_df.groupby(["PERIOD_YEAR_MONTH"]).agg({"abo_antall_tn": "sum", "rev_recur_tn": "sum", "rev_non_recur_tn": "sum", "abo_antall_vula": "sum", "rev_recur_vula": "sum", "rev_non_recur_vula": "sum"}).reset_index()
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