import pandas as pd
import streamlit as st

st.title("Auction Simulator")


st.header("Input Bids")
st.write("Enter the bids for each bidder in the fields below. 0 is a valid bid.")

st.header("Auction Parameters")
st.header("Total Supply")
supply = st.number_input("Total Supply (Number of Items Available)", min_value=1, value=7)


a_delta = 0.01
b_delta = 0.02
c_delta = -0.01
d_delta = -0.02
e_delta = -0.03

# minimum number of blocks won
st.header("Minimum Blocks Won Requirement")
min_blocks_won_a = st.number_input("Minimum Number of Blocks Won bidder 1", min_value=0, value=1, key="a")
min_blocks_won_b = st.number_input("Minimum Number of Blocks Won bidder 2", min_value=0, value=1, key="b")
min_blocks_won_c = st.number_input("Minimum Number of Blocks Won bidder 3", min_value=0, value=1, key="c")
min_blocks_won_d = st.number_input("Minimum Number of Blocks Won bidder 4", min_value=0, value=1, key="d")
min_blocks_won_e = st.number_input("Minimum Number of Blocks Won bidder 5", min_value=0, value=1, key="e")
minimum_blocks_won_df = pd.DataFrame(
    {
        "bidder_id": ["a", "b", "c", "d", "e"],
        "min_blocks_won": [min_blocks_won_a, min_blocks_won_b, min_blocks_won_c, min_blocks_won_d, min_blocks_won_e],
    }
)

def_bids_a = [10, 20, 30, 40, 50]
def_bids_b = [15, 25, 35, 45, 55]
def_bids_c = [12, 22, 32, 42, 52]
def_bids_d = [18, 28, 38, 48, 58]
def_bids_e = [14, 24, 34, 44, 54]
col_1, col_2, col_3, col_4, col_5 = st.columns(5)
st.header("Bidder 1: Package Valuations and Item Bids")
package_valuation_a1 = col_1.number_input("Package Valuation Bidder 1, item 1", min_value=0, value=def_bids_a[0])
package_valuation_a2 = col_2.number_input(
    "Package Valuation Bidder 1, item 1-2", min_value=0, value=(def_bids_a[0] + def_bids_a[1])
)
package_valuation_a3 = col_3.number_input(
    "Package Valuation Bidder 1, item 1-3", min_value=0, value=(def_bids_a[0] + def_bids_a[1] + def_bids_a[2])
)
package_valuation_a4 = col_4.number_input(
    "Package Valuation Bidder 1, item 1-4",
    min_value=0,
    value=(def_bids_a[0] + def_bids_a[1] + def_bids_a[2] + def_bids_a[3]),
)
package_valuation_a5 = col_5.number_input(
    "Package Valuation Bidder 1, item 1-5",
    min_value=0,
    value=(def_bids_a[0] + def_bids_a[1] + def_bids_a[2] + def_bids_a[3] + def_bids_a[4]),
)
a1 = col_1.number_input("Bidder 1 - Item 1", min_value=0, value=def_bids_a[0]) + a_delta
a2 = col_2.number_input("Bidder 1 - Item 2", min_value=0, value=def_bids_a[1]) + a_delta
a3 = col_3.number_input("Bidder 1 - Item 3", min_value=0, value=def_bids_a[2]) + a_delta
a4 = col_4.number_input("Bidder 1 - Item 4", min_value=0, value=def_bids_a[3]) + a_delta
a5 = col_5.number_input("Bidder 1 - Item 5", min_value=0, value=def_bids_a[4]) + a_delta

st.header("Bidder 2: Package Valuations and Item Bids")
package_valuation_b1 = col_1.number_input("Package Valuation Bidder 2, item 1", min_value=0, value=def_bids_b[0])
package_valuation_b2 = col_2.number_input(
    "Package Valuation Bidder 2, item 1-2", min_value=0, value=(def_bids_b[0] + def_bids_b[1])
)
package_valuation_b3 = col_3.number_input(
    "Package Valuation Bidder 2, item 1-3", min_value=0, value=(def_bids_b[0] + def_bids_b[1] + def_bids_b[2])
)
package_valuation_b4 = col_4.number_input(
    "Package Valuation Bidder 2, item 1-4",
    min_value=0,
    value=(def_bids_b[0] + def_bids_b[1] + def_bids_b[2] + def_bids_b[3]),
)
package_valuation_b5 = col_5.number_input(
    "Package Valuation Bidder 2, item 1-5",
    min_value=0,
    value=(def_bids_b[0] + def_bids_b[1] + def_bids_b[2] + def_bids_b[3] + def_bids_b[4]),
)
b1 = col_1.number_input("Bidder 2 - Item 1", min_value=0, value=def_bids_b[0]) + b_delta
b2 = col_2.number_input("Bidder 2 - Item 2", min_value=0, value=def_bids_b[1]) + b_delta
b3 = col_3.number_input("Bidder 2 - Item 3", min_value=0, value=def_bids_b[2]) + b_delta
b4 = col_4.number_input("Bidder 2 - Item 4", min_value=0, value=def_bids_b[3]) + b_delta
b5 = col_5.number_input("Bidder 2 - Item 5", min_value=0, value=def_bids_b[4]) + b_delta

st.header("Bidder 3: Package Valuations and Item Bids")
package_valuation_c1 = col_1.number_input("Package Valuation Bidder 3, item 1", min_value=0, value=def_bids_c[0])
package_valuation_c2 = col_2.number_input(
    "Package Valuation Bidder 3, item 1-2", min_value=0, value=(def_bids_c[0] + def_bids_c[1])
)
package_valuation_c3 = col_3.number_input(
    "Package Valuation Bidder 3, item 1-3", min_value=0, value=(def_bids_c[0] + def_bids_c[1] + def_bids_c[2])
)
package_valuation_c4 = col_4.number_input(
    "Package Valuation Bidder 3, item 1-4",
    min_value=0,
    value=(def_bids_c[0] + def_bids_c[1] + def_bids_c[2] + def_bids_c[3]),
)
package_valuation_c5 = col_5.number_input(
    "Package Valuation Bidder 3, item 1-5",
    min_value=0,
    value=(def_bids_c[0] + def_bids_c[1] + def_bids_c[2] + def_bids_c[3] + def_bids_c[4]),
)
c1 = col_1.number_input("Bidder 3 - Item 1", min_value=0, value=def_bids_c[0]) + c_delta
c2 = col_2.number_input("Bidder 3 - Item 2", min_value=0, value=def_bids_c[1]) + c_delta
c3 = col_3.number_input("Bidder 3 - Item 3", min_value=0, value=def_bids_c[2]) + c_delta
c4 = col_4.number_input("Bidder 3 - Item 4", min_value=0, value=def_bids_c[3]) + c_delta
c5 = col_5.number_input("Bidder 3 - Item 5", min_value=0, value=def_bids_c[4]) + c_delta

st.header("Bidder 4: Package Valuations and Item Bids")
package_valuation_d1 = col_1.number_input("Package Valuation Bidder 4, item 1", min_value=0, value=def_bids_d[0])
package_valuation_d2 = col_2.number_input(
    "Package Valuation Bidder 4, item 1-2", min_value=0, value=(def_bids_d[0] + def_bids_d[1])
)
package_valuation_d3 = col_3.number_input(
    "Package Valuation Bidder 4, item 1-3", min_value=0, value=(def_bids_d[0] + def_bids_d[1] + def_bids_d[2])
)
package_valuation_d4 = col_4.number_input(
    "Package Valuation Bidder 4, item 1-4",
    min_value=0,
    value=(def_bids_d[0] + def_bids_d[1] + def_bids_d[2] + def_bids_d[3]),
)
package_valuation_d5 = col_5.number_input(
    "Package Valuation Bidder 4, item 1-5",
    min_value=0,
    value=(def_bids_d[0] + def_bids_d[1] + def_bids_d[2] + def_bids_d[3] + def_bids_d[4]),
)
d1 = col_1.number_input("Bidder 4 - Item 1", min_value=0, value=def_bids_d[0]) + d_delta
d2 = col_2.number_input("Bidder 4 - Item 2", min_value=0, value=def_bids_d[1]) + d_delta
d3 = col_3.number_input("Bidder 4 - Item 3", min_value=0, value=def_bids_d[2]) + d_delta
d4 = col_4.number_input("Bidder 4 - Item 4", min_value=0, value=def_bids_d[3]) + d_delta
d5 = col_5.number_input("Bidder 4 - Item 5", min_value=0, value=def_bids_d[4]) + d_delta

st.header("Bidder 5: Package Valuations and Item Bids")
package_valuation_e1 = col_1.number_input("Package Valuation Bidder 5, item 1", min_value=0, value=def_bids_e[0])
package_valuation_e2 = col_2.number_input(
    "Package Valuation Bidder 5, item 1-2", min_value=0, value=(def_bids_e[0] + def_bids_e[1])
)
package_valuation_e3 = col_3.number_input(
    "Package Valuation Bidder 5, item 1-3", min_value=0, value=(def_bids_e[0] + def_bids_e[1] + def_bids_e[2])
)
package_valuation_e4 = col_4.number_input(
    "Package Valuation Bidder 5, item 1-4",
    min_value=0,
    value=(def_bids_e[0] + def_bids_e[1] + def_bids_e[2] + def_bids_e[3]),
)
package_valuation_e5 = col_5.number_input(
    "Package Valuation Bidder 5, item 1-5",
    min_value=0,
    value=(def_bids_e[0] + def_bids_e[1] + def_bids_e[2] + def_bids_e[3] + def_bids_e[4]),
)
e1 = col_1.number_input("Bidder 5 - Item 1", min_value=0, value=def_bids_e[0]) + e_delta
e2 = col_2.number_input("Bidder 5 - Item 2", min_value=0, value=def_bids_e[1]) + e_delta
e3 = col_3.number_input("Bidder 5 - Item 3", min_value=0, value=def_bids_e[2]) + e_delta
e4 = col_4.number_input("Bidder 5 - Item 4", min_value=0, value=def_bids_e[3]) + e_delta
e5 = col_5.number_input("Bidder 5 - Item 5", min_value=0, value=def_bids_e[4]) + e_delta

all_bids = {
    "a1": a1,
    "a2": a2,
    "a3": a3,
    "a4": a4,
    "a5": a5,
    "b1": b1,
    "b2": b2,
    "b3": b3,
    "b4": b4,
    "b5": b5,
    "c1": c1,
    "c2": c2,
    "c3": c3,
    "c4": c4,
    "c5": c5,
    "d1": d1,
    "d2": d2,
    "d3": d3,
    "d4": d4,
    "d5": d5,
    "e1": e1,
    "e2": e2,
    "e3": e3,
    "e4": e4,
    "e5": e5,
}

all_bids_df = pd.DataFrame(list(all_bids.items()), columns=["Bidder_Item", "Bid_Amount"])
ranked_bids = all_bids_df.sort_values(by="Bid_Amount", ascending=False).reset_index(drop=True)
st.header("All Bids")
st.dataframe(all_bids)
st.write("The bids are ranked from highest to lowest.")
st.dataframe(ranked_bids)

price = ranked_bids.iloc[supply + 1]["Bid_Amount"]
winners = ranked_bids[ranked_bids.index < (supply)]
winners["bidder_id"] = winners["Bidder_Item"].str[0]
winners["item_id"] = winners["Bidder_Item"].str[1]
winner_allocation = winners.groupby("bidder_id").size().reset_index(name="num_items_won_pre_min_check")
winner_allocation["unit_price"] = price
winner_allocation = winner_allocation.merge(minimum_blocks_won_df, on="bidder_id", how="left")
winner_allocation["meets_min_blocks_won"] = (
    winner_allocation["num_items_won_pre_min_check"] >= winner_allocation["min_blocks_won"]
)
winner_allocation["blocks_won_post_min_check"] = (
    winner_allocation["num_items_won_pre_min_check"] * winner_allocation["meets_min_blocks_won"]
)
winner_allocation["final_payment"] = winner_allocation["blocks_won_post_min_check"] * winner_allocation["unit_price"]


st.header("Final Winners and Allocation post minimum blocks won check")
st.dataframe(winner_allocation)
