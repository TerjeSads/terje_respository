# --- Imports ---
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from common.data_queries import general_bigquery_query

DEFAULT_PRODUCTS_LIST = ["2292", "12292", "9955", "19955", "9990", "9950", "229201", "102292"]

geo_dict = {
    "Postnummer": ["postcode", "post_office"],
    "Kommune": ["kommune_id", "kommune"],
    "Fylke": ["fylke_id", "fylke"],
    "Nasjonalt": ["country"],
}


@st.cache_data()
def invoice_postcode_query(year) -> str:
    return f"""
SELECT
  vpps.PERIOD_YEAR_MONTH,
  LEFT(cast(vpps.PERIOD_YEAR_MONTH as STRING),4) as year,
  RIGHT(cast(vpps.PERIOD_YEAR_MONTH as STRING),2) as month,
  "Norway" AS country,
  vpps.product_id,
  vpps.product_name,
  vpps.subscription_package_ids,
  vpps.subscription_package,
  vpps.billing_segment,
  vpps.fylke,
  vpps.fylke_id,
  vpps.kommune,
  vpps.kommune_id,
  vpps.postcode,
  vpps.post_office,
  sum(vpps.rev_non_recur) AS rev_non_rec,
  sum(vpps.rev_recur) AS rev_rec,
  sum(vpps.total_rev) AS rev_tot,
  sum(vpps.unique_subs) AS unique_subs,
  sum(vpps.observations) AS observations
FROM
  `spectrum-analytics-secure.fiber_rev_no_test_mirror.VI_PRODUCT_POSTNR_SUMMARY_MAT`
    AS vpps
WHERE
  vpps.PERIOD_YEAR_MONTH in ({", ".join(str(int(f"{year}{month:02d}")) for month in range(1, 13))})
  AND vpps.billing_segment = 'SDU'
GROUP BY ALL
      """


@st.cache_data()
def invoice_year_month_query() -> str:
    return """
SELECT DISTINCT PERIOD_YEAR_MONTH
FROM `spectrum-analytics-secure.fiber_rev_no_test_mirror.VI_PRODUCT_POSTNR_SUMMARY_MAT`
ORDER BY PERIOD_YEAR_MONTH DESC
"""


@st.cache_data()
def get_invoice_postcode_data(year_month: int) -> pd.DataFrame:
    query = invoice_postcode_query(year_month)
    return general_bigquery_query(query)


@st.cache_data()

# calculate total subscribers per subscription package per month
def calculate_total_subscribers(_df: pd.DataFrame, geo_level) -> pd.DataFrame:
    subscription_df = (
        _df.groupby(["PERIOD_YEAR_MONTH", "subscription_package_ids", "subscription_package", "product_id"] + geo_level)
        .agg({"unique_subs": "sum"})
        .reset_index()
    )
    subscription_subs_df = (
        subscription_df.groupby(
            ["PERIOD_YEAR_MONTH", "subscription_package_ids", "subscription_package"] + geo_level, as_index=False
        )
        .agg({"unique_subs": "max"})
        .rename(columns={"unique_subs": "total_subs"})
    )
    return subscription_subs_df


# Create product selection
def create_ordered_product_dict(_df: pd.DataFrame) -> dict:
    products = _df[["product_id", "product_name"]].drop_duplicates().astype(str)
    products_sorted = products.sort_values(by="product_name", ascending=True)
    product_dict = dict(zip(products_sorted["product_id"], products_sorted["product_name"]))
    default_product_list_filtered = [pid for pid in DEFAULT_PRODUCTS_LIST if pid in product_dict.keys()]

    return product_dict, default_product_list_filtered


def pivot_table_printer(_df: pd.DataFrame, column_name: str, index_name: list) -> pd.DataFrame:
    _df_pivot = _df.pivot_table(index=index_name, columns="PERIOD_YEAR_MONTH", values=column_name, fill_value=0)

    if column_name != "avg_rev_per_sub":
        _df_pivot = _df_pivot.reindex(["Total"] + _df_pivot.index.tolist())
        _df_pivot.loc["Total"] = _df_pivot.sum(numeric_only=True)
    return _df_pivot


def number_formatter(_df):
    styled = _df.style.format(subset=_df.columns, formatter="{:,.0f}", na_rep="0")
    # Apply grey background to "Totale rabatter, NOK" columns
    if isinstance(_df.columns, pd.MultiIndex):
        totale_rabatter_cols = [col for col in _df.columns if col[0] == "Totale rabatter, NOK"]
        if totale_rabatter_cols:
            styled = styled.set_properties(subset=totale_rabatter_cols, **{"background-color": "#e0e0e0"})
    return styled


###################################
year_month_options = general_bigquery_query(invoice_year_month_query())
current_yr_month = int(datetime.now().strftime("%Y%m"))
year_month_options = year_month_options[year_month_options["PERIOD_YEAR_MONTH"] <= current_yr_month]
year_month_options = year_month_options["PERIOD_YEAR_MONTH"].tolist()

st.title("Fiber SDU - Rabatt per geografi")

year_selected = st.multiselect(
    "Velg faktureringsår:",
    options=[yr for yr in range(2022, datetime.now().year + 1)],
    default=[datetime.now().year - 1],
)


@st.cache_data()
def selected_year__data(_years: list) -> pd.DataFrame:
    lst_tmp = []
    for _yr in _years:
        df = get_invoice_postcode_data(_yr)
        lst_tmp.append(df)
    invoice_data_filtered = pd.concat(lst_tmp)
    invoice_data_filtered["subscription_package_ids"] = invoice_data_filtered["subscription_package_ids"].astype(str)
    invoice_data_filtered["subscription_package"] = invoice_data_filtered["subscription_package"].astype(str)

    return invoice_data_filtered


df_invoice_year = selected_year__data(year_selected)


selected_geo = st.selectbox(
    "Velg geografisk nivå for analyse:",
    options=list(geo_dict.keys()),
    index=3,
)

selected_geo_ids = geo_dict[selected_geo]
min_subs = st.slider(
    f"Minimum antall abonnenter på '{selected_geo}' nivå for å bli inkludert i analysen:",
    min_value=0,
    max_value=1000,
    value=100,
    step=10,
)

invoice_data_filtered_raw = selected_year__data(year_selected)
subscription_subs_df = calculate_total_subscribers(invoice_data_filtered_raw, selected_geo_ids)
product_dict, default_product_list_filtered = create_ordered_product_dict(invoice_data_filtered_raw)

national_df = (
    invoice_data_filtered_raw.groupby(["PERIOD_YEAR_MONTH", "subscription_package"], as_index=False)
    .agg({"rev_tot": "sum", "unique_subs": "sum"})
    .merge(subscription_subs_df, on=["PERIOD_YEAR_MONTH", "subscription_package"], how="left")
)

national_gross_rev_piv = national_df.pivot_table(
    index=["subscription_package"], columns="PERIOD_YEAR_MONTH", values="rev_tot", fill_value=0
)
national_total_subs_piv = national_df.pivot_table(
    index=["subscription_package"], columns="PERIOD_YEAR_MONTH", values="total_subs", fill_value=0
)
# add sum row
national_gross_rev_piv = national_gross_rev_piv.reindex(["Total"] + national_gross_rev_piv.index.tolist())
national_gross_rev_piv.loc["Total"] = national_gross_rev_piv.sum(numeric_only=True)
national_total_subs_piv = national_total_subs_piv.reindex(["Total"] + national_total_subs_piv.index.tolist())
national_total_subs_piv.loc["Total"] = national_total_subs_piv.sum(numeric_only=True)
# Replace 0 with NaN in denominator to avoid division by zero, then replace result NaN with 0


national_net_arpu_pivot = national_gross_rev_piv.div(national_total_subs_piv.replace(0, np.nan)).fillna(0)

selected_product_ids = st.multiselect(
    "Velg produkt(er) for analyse:",
    options=list(product_dict.keys()),
    format_func=lambda x: product_dict[x],
    default=default_product_list_filtered,
)
selected_product_ids = [int(x) for x in selected_product_ids]

invoice_data_filtered = invoice_data_filtered_raw[invoice_data_filtered_raw["product_id"].isin(selected_product_ids)]

sub_per_month = (
    subscription_subs_df.groupby(["PERIOD_YEAR_MONTH", "subscription_package"], as_index=False)
    .agg({"total_subs": "max"})
    .groupby(["PERIOD_YEAR_MONTH"], as_index=False)
    .agg({"total_subs": "sum"})
)
national_total_rabatter = (
    invoice_data_filtered.groupby(["PERIOD_YEAR_MONTH", "product_name"], as_index=False)
    .agg({"rev_tot": "sum", "unique_subs": "sum"})
    .merge(sub_per_month, on=["PERIOD_YEAR_MONTH"], how="left")
)

national_rabatt_piv = national_total_rabatter.pivot_table(
    index=["product_name"], columns="PERIOD_YEAR_MONTH", values="rev_tot", fill_value=0
)
national_total_subs_rabatt_piv = national_total_rabatter.pivot_table(
    index=["product_name"], columns="PERIOD_YEAR_MONTH", values="total_subs", fill_value=0
)
# add sum row
national_rabatt_piv = national_rabatt_piv.reindex(["Total"] + national_rabatt_piv.index.tolist())
national_rabatt_piv.loc["Total"] = national_rabatt_piv.sum(numeric_only=True)

national_total_subs_rabatt_piv = national_total_subs_rabatt_piv.reindex(
    ["Total"] + national_total_subs_rabatt_piv.index.tolist()
)
national_total_subs_rabatt_piv.loc["Total"] = national_total_subs_rabatt_piv.mean(numeric_only=True)
# Replace 0 with NaN in denominator to
national_avg_rabatt_piv = national_rabatt_piv.div(national_total_subs_rabatt_piv.replace(0, np.nan)).fillna(0)


invoice_data_grp = invoice_data_filtered.groupby(
    ["PERIOD_YEAR_MONTH", "subscription_package"] + selected_geo_ids, as_index=False
).agg(
    {
        "rev_tot": "sum",
        "unique_subs": "sum",
    }
)

invoice_data_grp = (
    invoice_data_grp.merge(
        subscription_subs_df, on=["PERIOD_YEAR_MONTH", "subscription_package"] + selected_geo_ids, how="left"
    )
    .groupby(["PERIOD_YEAR_MONTH"] + selected_geo_ids, as_index=False)
    .agg({"rev_tot": "sum", "unique_subs": "sum", "total_subs": "sum"})
)

invoice_data_grp["avg_rev_per_sub"] = invoice_data_grp["rev_tot"] / invoice_data_grp["total_subs"]
invoice_data_grp = invoice_data_grp.query("total_subs >= @min_subs")


with st.expander(
    "Nasjonal oppsummering av netto ARPU, totalt antall abonnenter og netto inntekter, og rabatter for valgte produkter",
    expanded=False,
):
    st.subheader("Nasjonal netto ARPU")
    st.dataframe(number_formatter(national_net_arpu_pivot))
    st.subheader("Nasjonalt totalt antall abonnenter")
    st.dataframe(number_formatter(national_total_subs_piv))
    st.subheader("Nasjonal netto inntekter")
    st.dataframe(number_formatter(national_gross_rev_piv))
    st.subheader("Nasjonal gjennomsnittlig rabatt per abonnent for valgte produkter")
    st.dataframe(number_formatter(national_avg_rabatt_piv))
    st.subheader("Nasjonal totale rabatter for valgte produkter")
    st.dataframe(number_formatter(national_rabatt_piv))
    st.subheader("Nasjonalt antall abonnenter for valgte produkter")
    st.dataframe(number_formatter(national_total_subs_rabatt_piv))

st.subheader(
    f"Gjennomsnittlig rabatt per abonnent i valgt geografisk nivå: {selected_geo.capitalize()} med minimum {min_subs} abonnenter"
)

geo_level_piv = pivot_table_printer(invoice_data_grp, "total_subs", selected_geo_ids)
geo_rev_tot_piv = pivot_table_printer(invoice_data_grp, "rev_tot", selected_geo_ids)
geo_avg_rev_piv = geo_rev_tot_piv.div(geo_level_piv.replace(0, np.nan)).fillna(0)
geo_avg_rev_piv = geo_avg_rev_piv.sort_values(by=invoice_data_grp["PERIOD_YEAR_MONTH"].max(), ascending=True)
idx = geo_avg_rev_piv.index.tolist()

geo_avg_rev_piv_display = geo_avg_rev_piv.reindex(idx).fillna(0)
geo_avg_rev_piv_display.columns = pd.MultiIndex.from_product(
    [["Average rabatt per subscriber, NOK"], geo_avg_rev_piv_display.columns]
)

geo_rev_tot_piv_display = geo_rev_tot_piv.reindex(idx).fillna(0)
geo_rev_tot_piv_display.columns = pd.MultiIndex.from_product(
    [["Totale rabatter, NOK"], geo_rev_tot_piv_display.columns]
)

geo_level_piv_display = geo_level_piv.reindex(idx).fillna(0)
geo_level_piv_display.columns = pd.MultiIndex.from_product([["Totale kunder"], geo_level_piv_display.columns])

geo_all_df_merged = pd.concat([geo_avg_rev_piv_display, geo_rev_tot_piv_display, geo_level_piv_display], axis=1)
geo_all_df_merged = geo_all_df_merged.fillna(0)
st.dataframe(number_formatter(geo_all_df_merged))
# subscription package level analysis for selected geo level and min_subs
st.subheader("Abonnementspakke nivå analyse for utvalgt geografi")

if selected_geo == "Nasjonalt":
    geo_area_options = invoice_data_filtered_raw["country"].unique().tolist()
else:
    geo_area_options = invoice_data_filtered_raw[selected_geo_ids[1]].unique().tolist()

selected_area = st.selectbox("Velg område for tidsserieanalyse:", options=geo_area_options)

if selected_geo == "Nasjonalt":
    unique_id_numb = "Norway"
else:
    if (
        len(
            invoice_data_filtered_raw[invoice_data_filtered_raw[selected_geo_ids[1]] == selected_area][
                selected_geo_ids[0]
            ].unique()
        )
        > 1
    ):
        relevant_ids = invoice_data_filtered_raw[invoice_data_filtered_raw[selected_geo_ids[1]] == selected_area][
            selected_geo_ids[0]
        ].unique()
        unique_id_numb = st.selectbox("Velg spesifikt ID for området:", options=relevant_ids)
    else:
        unique_id_numb = invoice_data_filtered_raw[invoice_data_filtered_raw[selected_geo_ids[1]] == selected_area][
            selected_geo_ids[0]
        ].unique()[0]
        st.text(f"Valgt område har unikt ID: {unique_id_numb}")

selected_area_df = invoice_data_filtered_raw[invoice_data_filtered_raw[selected_geo_ids[0]] == unique_id_numb]
selected_area_df = selected_area_df[selected_area_df["product_id"].isin(selected_product_ids)]

invoice_data_subscription = selected_area_df.groupby(
    ["PERIOD_YEAR_MONTH", "subscription_package"] + selected_geo_ids, as_index=False
).agg(
    {
        "rev_tot": "sum",
        "unique_subs": "sum",
    }
)

invoice_data_subscription = (
    invoice_data_subscription.merge(
        subscription_subs_df, on=["PERIOD_YEAR_MONTH", "subscription_package"] + selected_geo_ids, how="left"
    )
    .groupby(["PERIOD_YEAR_MONTH", "subscription_package"] + selected_geo_ids, as_index=False)
    .agg({"rev_tot": "sum", "unique_subs": "sum", "total_subs": "sum"})
)

invoice_data_subscription["avg_rev_per_sub"] = (
    invoice_data_subscription["rev_tot"] / invoice_data_subscription["total_subs"]
)


tot_subs_selected_df = pivot_table_printer(
    _df=invoice_data_subscription, column_name="total_subs", index_name=["subscription_package"]
)


tot_subs_selected_df_display = tot_subs_selected_df.fillna(0).copy()
tot_subs_selected_df_display.columns = pd.MultiIndex.from_product(
    [["Totale kunder"], tot_subs_selected_df_display.columns]
)

rev_tot_selected_df = pivot_table_printer(invoice_data_subscription, "rev_tot", index_name=["subscription_package"])
rev_tot_selected_df_display = rev_tot_selected_df.fillna(0).copy()
rev_tot_selected_df_display.columns = pd.MultiIndex.from_product(
    [["Totale rabatter, NOK"], rev_tot_selected_df_display.columns]
)

# Replace 0 with NaN in denominator to avoid division by zero, then replace result NaN with 0
avg_tot_selected_df = rev_tot_selected_df.div(tot_subs_selected_df.replace(0, np.nan))
avg_tot_selected_df_display = avg_tot_selected_df.fillna(0).copy()
avg_tot_selected_df_display.columns = pd.MultiIndex.from_product(
    [["Average rabatt per subscriber, NOK"], avg_tot_selected_df_display.columns]
)

all_df_merged = pd.concat(
    [avg_tot_selected_df_display, rev_tot_selected_df_display, tot_subs_selected_df_display], axis=1
)
all_df_merged = all_df_merged.fillna(0)
st.dataframe(number_formatter(all_df_merged))

_col_21, _col_22, _col_23 = st.columns(3)
