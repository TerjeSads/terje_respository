import streamlit as st

st.set_page_config(page_title="ADS Template App", layout="wide")
st.header("Hello World")
st.warning("This is a template app. Please change me!")

pg = st.navigation(
    [
        st.Page("gui_pages/page1.py", title="Home", default=True),
        st.Page("gui_pages/page2.py", title="Page 2"),
        st.Page("gui_pages/ssb_report.py", title="SSB Consumer Prices"),
        st.Page("gui_pages/auction_simulator.py", title="Auction Simulator"),
    ]
)
pg.run()
