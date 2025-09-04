import streamlit as st
from sadsapi.financial import get_company_info

from common.data_queries import example_bigquery_function, example_sql_function

st.subheader("This is page 1")
st.info("We perform some sample queries to show that the connectivity works.")

with st.expander("### SQL Server", expanded=True):
    st.dataframe(example_sql_function("NO"))
with st.expander("### BigQuery", expanded=True):
    st.dataframe(example_bigquery_function("Norway"))
with st.expander("### SADSAPI", expanded=True):
    st.dataframe(get_company_info())
