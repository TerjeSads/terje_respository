
import streamlit as st
import pandas as pd

st.title("Auction Simulator")


st.header("Input Bids")
st.write("Enter the bids for each bidder in the fields below. Leave a field empty if")

supply = st.number_input("Total Supply (Number of Items Available)", min_value=1, value=7)

col_1, col_2, col_3, col_4, col_5 = st.columns(5)
a_delta = 0.01
b_delta = 0.02
c_delta = -0.01
d_delta = -0.02
e_delta = -0.03

def_bids_a = [10, 20, 30, 40, 50]
def_bids_b = [15, 25, 35, 45, 55]
def_bids_c = [12, 22, 32, 42, 52]
def_bids_d = [18, 28, 38, 48, 58]
def_bids_e = [14, 24, 34, 44, 54]

a1=col_1.number_input("Bidder 1 - Item 1", min_value=0, value=def_bids_a[0])+a_delta
a2=col_2.number_input("Bidder 1 - Item 2", min_value=0, value=def_bids_a[1])+a_delta
a3=col_3.number_input("Bidder 1 - Item 3", min_value=0, value=def_bids_a[2])+a_delta
a4=col_4.number_input("Bidder 1 - Item 4", min_value=0, value=def_bids_a[3])+a_delta
a5=col_5.number_input("Bidder 1 - Item 5", min_value=0, value=def_bids_a[4])+a_delta

b1=col_1.number_input("Bidder 2 - Item 1", min_value=0, value=def_bids_b[0])+b_delta
b2=col_2.number_input("Bidder 2 - Item 2", min_value=0, value=def_bids_b[1])+b_delta
b3=col_3.number_input("Bidder 2 - Item 3", min_value=0, value=def_bids_b[2])+b_delta
b4=col_4.number_input("Bidder 2 - Item 4", min_value=0, value=def_bids_b[3])+b_delta
b5=col_5.number_input("Bidder 2 - Item 5", min_value=0, value=def_bids_b[4])+b_delta

c1=col_1.number_input("Bidder 3 - Item 1", min_value=0, value=def_bids_c[0])+c_delta
c2=col_2.number_input("Bidder 3 - Item 2", min_value=0, value=def_bids_c[1])+c_delta
c3=col_3.number_input("Bidder 3 - Item 3", min_value=0, value=def_bids_c[2])+c_delta
c4=col_4.number_input("Bidder 3 - Item 4", min_value=0, value=def_bids_c[3])+c_delta
c5=col_5.number_input("Bidder 3 - Item 5", min_value=0, value=def_bids_c[4])+c_delta

d1=col_1.number_input("Bidder 4 - Item 1", min_value=0, value=def_bids_d[0])+d_delta
d2=col_2.number_input("Bidder 4 - Item 2", min_value=0, value=def_bids_d[1])+d_delta
d3=col_3.number_input("Bidder 4 - Item 3", min_value=0, value=def_bids_d[2])+d_delta
d4=col_4.number_input("Bidder 4 - Item 4", min_value=0, value=def_bids_d[3])+d_delta
d5=col_5.number_input("Bidder 4 - Item 5", min_value=0, value=def_bids_d[4])+d_delta

e1=col_1.number_input("Bidder 5 - Item 1", min_value=0, value=def_bids_e[0])+e_delta
e2=col_2.number_input("Bidder 5 - Item 2", min_value=0, value=def_bids_e[1])+e_delta
e3=col_3.number_input("Bidder 5 - Item 3", min_value=0, value=def_bids_e[2])+e_delta
e4=col_4.number_input("Bidder 5 - Item 4", min_value=0, value=def_bids_e[3])+e_delta
e5=col_5.number_input("Bidder 5 - Item 5", min_value=0, value=def_bids_e[4])+e_delta

all_bids = {"a1": a1, "a2": a2, "a3": a3, "a4": a4, "a5": a5,
            "b1": b1, "b2": b2, "b3": b3, "b4": b4, "b5": b5,
            "c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5,
            "d1": d1, "d2": d2, "d3": d3, "d4": d4, "d5": d5,
            "e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5
}


all_bids_df = pd.DataFrame(list(all_bids.items()), columns=['Bidder_Item', 'Bid_Amount'])
ranked_bids = all_bids_df.sort_values(by='Bid_Amount', ascending=False).reset_index(drop=True)
st.header("All Bids")
st.dataframe(all_bids)
st.write("The bids are ranked from highest to lowest.")
st.dataframe(ranked_bids)

price = ranked_bids.iloc[supply+1]["Bid_Amount"]
winners = ranked_bids[ranked_bids.index < (supply)]
winners["bidder_id"] = winners["Bidder_Item"].str[0]
winners["item_id"] = winners["Bidder_Item"].str[1]
winner_allocation = winners.groupby("bidder_id").size().reset_index(name='num_items_won')
winner_allocation["unit_price"] = price
st.dataframe(winner_allocation)
