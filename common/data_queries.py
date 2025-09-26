from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pyjstat
import requests
import streamlit as st
from google.cloud import bigquery
from sqlalchemy import TextClause, text

from common.connectivity import bq_client, sql_engine

# We need to use st.cache_data to cache the results of the queries
# This, however, is automatically done on the API client library side
# so we only need to do it for the  queries here


@st.cache_data
def example_sql_function(country_code: str) -> pd.DataFrame:
    query: TextClause = text(
        """SELECT
            country_code, mnc, network_name_detailed
        FROM
            financial_forecast.mobile_network_detailed
        WHERE country_code = :cc"""
    )
    try:
        return pd.read_sql(
            query,
            con=sql_engine,
            params={"cc": country_code},
        )
    except Exception as e:
        st.error(f"An error occurred while querying the SQL database: {e}")
        return pd.DataFrame()


@st.cache_data
def example_bigquery_function(country: str) -> pd.DataFrame:
    query_string = """
    SELECT topic, sub_topic, COUNT(*) AS counter
    FROM `spectrum-analytics-secure.facebook_insights.dashboard_data`
    WHERE
        country = @country
    GROUP BY ALL
    """
    try:
        return bq_client.query_and_wait(
            query_string,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("country", "STRING", country)]
            ),
        ).to_dataframe()
    except Exception as e:
        st.error(f"An error occurred while querying BigQuery: {e}")
        return pd.DataFrame()
    
@st.cache_data

def fetch_ssb_cpi_and_subaggregates():
    """
    Fetches Consumer Price Index (CPI) and sub-aggregates from SSB Norway's API.
    Returns a pandas DataFrame with the results.
    """
    # SSB API endpoint for CPI (table 03013)
    url = "https://data.ssb.no/api/v0/no/table/03013/"
    # Example query for all CPI and sub-aggregates
    query = {
  "query": [
    {
      "code": "Konsumgrp",
      "selection": {
        "filter": "vs:CoiCop2016niva1",
        "values": [
          "TOTAL"
        ]
      }
    },
    {
      "code": "ContentsCode",
      "selection": {
        "filter": "item",
        "values": [
          "KpiIndMnd",
          "Manedsendring",
          "Tolvmanedersendring"
        ]
      }
    }
  ],
  "response": {
    "format": "json-stat2"
  }
}
    try:
        @st.cache_data()
        resul = requests.post(url, json=query)
        dataset = pyjstat.Dataset.read(resultat.text)
        raw_df: pd.DataFrame = dataset.write("dataframe")
        
        return df
    except Exception as e:
        st.error(f"Failed to fetch CPI data from SSB: {e}")
        return pd.DataFrame()


