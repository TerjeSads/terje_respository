import streamlit as st

st.set_page_config(page_title="ADS Template App", layout="wide")

pg = st.navigation(
    [
        st.Page("gui_pages/auction_simulator.py", title="Auction Simulator"),
        st.Page("gui_pages/geo_tn_vula_arpu.py", title="TN and VULA ARPU Data"),
    ]
)
pg.run()
