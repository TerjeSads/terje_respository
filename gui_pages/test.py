from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from common.data_queries import general_bigquery_query


def invoice_postcode_query() -> str:
    return """
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
  vpps.PERIOD_YEAR_MONTH in (202501, 202502, 202503,202504, 202505, 202506, 202507, 202508, 202509, 202510, 202511, 202512)
  AND vpps.billing_segment = 'SDU'
GROUP BY ALL
      """


def get_invoice_postcode_data() -> pd.DataFrame:
    query = invoice_postcode_query()
    return general_bigquery_query(query)


data = (
    get_invoice_postcode_data().groupby(["year", "month"]).agg({"rev_tot": "sum", "unique_subs": "sum"}).reset_index()
)
st.dataframe(data)
