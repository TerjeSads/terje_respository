import datetime as dt

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sads_api_schemas.enums import FinanceKPIs, Periodicity, QueryMetric
from sads_api_schemas.request.input_classes import SpectrumRequest
from sadsapi.financial import get_company_info
from sadsapi.gsmai import get_datasets, get_gsmai_data
from sadsapi.spectrum.confidential import make_spectrum_api_call

comp_info = get_company_info()
telenor_ops = comp_info[(comp_info["group_id"] == 1) & (comp_info["network_id"] > 1)]
operator_dict = {
    "Telenor BUs": [1, 12, 21, 22, 25, 28, 79],
    "BD": [1, 2, 3],
    "PK": [12, 13, 14, 15],
    "FI": [19, 20, 21],
    "SE": [22, 32, 23, 24],
    "DK": [25, 31, 26, 27],
    "NO": [28, 29, 30],
    "Grameenphone": [1],
    "Telenor Norway": [28],
    "Telenor Sweden": [22],
    "Telenor Denmark": [25],
    "Telenor Finland": [21],
    "Telenor Pakistan": [12],
}


country_dict = {
    "NO": "Norway",
    "SE": "Sweden",
    "DK": "Denmark",
    "FI": "Finland",
    "MY": "Malaysia",
    "TH": "Thailand",
    "DE": "Germany",
    "IT": "Italy",
    "FR": "France",
    "ES": "Spain",
    "GB": "United Kingdom",
    "US": "United States of America",
    "SI": "Slovenia",
    "HU": "Hungary",
    "PT": "Portugal",
    "GR": "Greece",
    "AT": "Austria",
    "BE": "Belgium",
    "NL": "Netherlands",
    "CH": "Switzerland",
    "IE": "Ireland",
    "CZ": "Czechia",
    "SK": "Slovakia",
    "PL": "Poland",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "RS": "Serbia",
    "RU": "Russian Federation",
    "TR": "Türkiye",
    "TW": "Taiwan; Province of China",
    "HK": "Hong Kong; SAR China",
    "SG": "Singapore",
    "AU": "Australia",
    "NZ": "New Zealand",
    "RO": "Romania",
    "LV": "Latvia",
    "LT": "Lithuania",
    "BD": "Bangladesh",
    "PK": "Pakistan",
    "CA": "Canada",
    "ID": "Indonesia",
    "SL": "Sri Lanka",
    "IS": "Iceland",
    "MM": "Myanmar",
    "UA": "Ukraine",
    "EE": "Estonia",
    "EG": "Egypt",
    "IN": "India",
    "KR": "Korea; South",
    "ME": "Montenegro",
}

item_list = [
    "Total revenue; cellular",
    "ARPU; by unique mobile subscriber",
    "Total population",
    "GDP per capita",
    "GDP per capita in PPP",
]


def spend_annual_fee_creator(metric, financial_measure, start_year, end_year, key):
    operator_list = tn_op_lst
    periodicity = Periodicity.Annual

    detailed_outputs = True
    extrapolation_fx_calc_date = None

    emp_lst = []
    for c in ["committed", "forecast"]:
        if c == "committed":
            include_forecast = False
            include_historic = True
        else:
            include_forecast = True
            include_historic = False

        req = SpectrumRequest(
            operators=operator_list,
            metric_query=metric,
            periodicity_query=periodicity,
            financial_metric=financial_measure,
            include_forecast=include_forecast,
            include_historic=include_historic,
            detailed=detailed_outputs,
            start_year=start_year,
            end_year=end_year,
            extrapolation_fx_calc_date=extrapolation_fx_calc_date,
        )

        spend_forecast_df_tmp = make_spectrum_api_call(req)
        spend_forecast_df_tmp["status"] = c
        emp_lst.append(spend_forecast_df_tmp)

    spend_forecast_df = pd.concat(emp_lst)

    spend_forecast_df["start_date"] = spend_forecast_df["start_date"].dt.year
    spend_forecast_df["stop_date"] = spend_forecast_df["stop_date"].dt.year
    spend_forecast_df["value"] /= 1000000
    spend_forecast_table = spend_forecast_df.pivot_table(
        index=[
            "country_name",
            "name",
            "operator_id",
            "reporting_currency_id",
            "status",
            "start_date",
            "stop_date",
            "band",
            "bandwidth",
        ],
        columns="year",
        values="value",
        fill_value=0,
    )
    spend_forecast_table["Total"] = spend_forecast_table.sum(axis=1)
    spend_forecast_table = spend_forecast_table[spend_forecast_table["Total"] > 0]

    totals = spend_forecast_table.sum(axis=0)
    totals.name = ("Total", "", "", "", "", "", "", "", "")
    spend_forecast_table = pd.concat([spend_forecast_table, totals.to_frame().T])

    row_cnt = len(spend_forecast_table)

    with st.expander("Spectrum spend forecast", expanded=False):
        st.subheader(
            f"Total {financial_measure.name.replace('_', ' ')} (million) in {metric.name[-3:]} for the period \
                {start_year}-{end_year}"
        )
        st.dataframe(spend_forecast_table.style.format("{:,.1f}"), height=35 * row_cnt + 38, use_container_width=True)
    with st.expander("Summary per country", expanded=False):
        st.subheader(
            f"Summary per country: Total {financial_measure.name.replace('_', ' ')} (million) in {metric.name[-3:]} \
                for the period {start_year}-{end_year}"
        )
        summary_spend_df = spend_forecast_table.groupby(["country_name"]).sum()
        st.dataframe(
            summary_spend_df.style.format("{:,.0f}"), height=35 * len(summary_spend_df) + 38, use_container_width=True
        )
    with st.expander("Summary per operator", expanded=False):
        st.subheader(
            f"Summary per operator: Total {financial_measure.name.replace('_', ' ')} (million) in {metric.name[-3:]} \
                for the period {start_year}-{end_year}"
        )
        country_list = spend_forecast_df["country_name"].unique()
        summary_op_spend_df = spend_forecast_table.groupby(
            [
                "country_name",
                "name",
            ]
        ).sum()
        for c in country_list:
            st.write(c)
            df_oper_plot = summary_op_spend_df[summary_op_spend_df.index.get_level_values(0) == c]
            if df_oper_plot.empty:
                st.markdown("<span style='color:red'> No data </span>", unsafe_allow_html=True)
                continue
            else:
                st.dataframe(
                    df_oper_plot.style.format("{:,.0f}"),
                    height=35 * len(df_oper_plot) + 38,
                    use_container_width=True,
                )

    per_mhz_table = spend_forecast_table.copy()

    with st.expander("Per MHz amount", expanded=False):
        st.subheader(
            f"Per MHz amount {financial_measure.name.replace('_', ' ')}\
                  in {metric.name[-3:]} for the period {start_year}\
            -{end_year}"
        )

        for i in range(len(spend_forecast_table)):
            per_mhz_table.to_numpy()[i] = (
                1000000 * spend_forecast_table.to_numpy()[i] / spend_forecast_table.index.get_level_values(8)[i]
            )

        st.dataframe(per_mhz_table.style.format("{:,.0f}"), height=35 * row_cnt + 38, use_container_width=True)

    summary_band_spend_df = (
        spend_forecast_df.groupby(["country_name", "name", "operator_id", "reporting_currency_id", "band", "year"])
        .agg({"value": "sum"})
        .reset_index()
    )

    for o in operator_list:
        plot_df = summary_band_spend_df[summary_band_spend_df["operator_id"] == o]
        op_name = plot_df["name"].unique()[0]
        curr = plot_df["reporting_currency_id"].unique()[0]
        country = plot_df["country_name"].unique()[0]
        fig = px.line(plot_df, x="year", y="value", color="band", height=1000)
        fig.update_layout(legend_title_text="Band", xaxis_title="Year")
        fig.update_yaxes(title_text="Value")
        fig.update_xaxes(dtick=1, title_text="Year")
        max_year = plot_df["year"].max()
        text_df = plot_df[
            (plot_df["year"] == max_year)
            | (plot_df["year"] == max_year - 2)
            | (plot_df["year"] == max_year - 6)
            | (plot_df["year"] == max_year - 8)
        ]
        fig.add_trace(
            go.Scatter(
                x=text_df["year"],
                y=text_df["value"],
                text=text_df["band"],
                mode="markers+text",
                textposition="top center",
                name="Band",
                showlegend=False,
            )
        )
        st.subheader(f"{op_name} ({o}) - {country} - {curr}, million")

        st.plotly_chart(fig, use_container_width=True, key=f"{key}_{o}")
    return spend_forecast_table


def start_expiry_table_creator(
    operator_list,
    metric,
    periodicity,
    include_forecast,
    include_historic,
    detailed_outputs,
    financial_measure,
    start_year,
    end_year,
    extrapolation_fx_calc_date,
):
    req = SpectrumRequest(
        operators=operator_list,
        metric_query=metric,
        periodicity_query=periodicity,
        financial_metric=financial_measure,
        include_forecast=include_forecast,
        include_historic=include_historic,
        detailed=detailed_outputs,
        start_year=start_year,
        end_year=end_year,
        extrapolation_fx_calc_date=extrapolation_fx_calc_date,
    )
    start_expiry_df = make_spectrum_api_call(req)
    return start_expiry_df


tab_GSAM_data, tab_spectrum_data, tab_fiber = st.tabs(["GSMAI", "Spectrum", "fiber"])

with tab_GSAM_data:
    tab_gsmai, tab_gsmai_selected = st.tabs(["GSMAI data", "GSMAI selected"])

    st.write("c")
    st.dataframe(get_datasets(lcu=False))
    with tab_gsmai:
        df_sets = get_datasets(lcu=False)
        st.dataframe(df_sets)
        index_default = df_sets["dataset_name"][df_sets["dataset_name"] == "Total revenue; cellular"].index[0].item()

        empty = []
        for i in item_list:
            data_set_id_selected = df_sets[df_sets["dataset_name"] == i]["dataset_id"].item()

            df_set_usd = get_gsmai_data(
                country=list(country_dict.keys()),
                lcu=False,
                dataset_id=data_set_id_selected,
                start_year=2008,
                end_year=2050,
                periodicity=Periodicity.Quarterly,
            )
            df_set_usd["item"] = i
            df_set_usd["country_name"] = df_set_usd["country_code"].map(country_dict)

            df_set_lcu = get_gsmai_data(
                country=list(country_dict.keys()),
                lcu=True,
                dataset_id=data_set_id_selected,
                start_year=2008,
                end_year=2050,
                periodicity=Periodicity.Quarterly,
            )

            df_set = df_set_usd.merge(
                df_set_lcu[["country_code", "year", "quarter", "value"]],
                on=["country_code", "year", "quarter"],
                suffixes=("_usd", "_lcu"),
            )
            df_set = df_set.sort_values(by=["country_code", "year", "quarter"])
            df_set["exc_rate"] = df_set["value_lcu"] / df_set["value_usd"]
            df_set["year_quarter"] = df_set["year"].astype(str) + "Q" + df_set["quarter"].astype(str)

            st.dataframe(df_set)
            df_set_pivot = df_set.pivot_table(
                index=["item", "country_code", "country_name"], columns="year_quarter", values="value_usd"
            )
            # df_set_pivot = df_set.pivot_table(
            #     index=["item", "country_code", "country_name"], columns="year_quarter", values="value_lcu"
            # )

            empty.append(df_set_pivot)

        df_gsmai_data = pd.concat(empty)
        st.dataframe(df_gsmai_data)

    with tab_gsmai_selected:
        data_set_name_selected = st.multiselect(
            "Select a dataset",
            df_sets["dataset_name"],
            default=["2G connections", "3G connections", "4G connections", "5G connections"],
        )
        data_set_name_selected = (
            list(data_set_name_selected) if len(data_set_name_selected) == 1 else data_set_name_selected
        )
        country_id_list_selected = st.multiselect(
            "Select countries", list(country_dict.keys()), default=["NO", "SE", "DK", "FI", "PK", "BD"]
        )
        lcu_selcted = st.checkbox("Select LCU", value=False)
        data_set_id_selected = list(df_sets[df_sets["dataset_name"].isin(data_set_name_selected)]["dataset_id"])

        emp_lst = []
        for i in data_set_id_selected:
            item_name = df_sets[df_sets["dataset_id"] == i]["dataset_name"].item()
            df_set_aux = get_gsmai_data(
                country=list(country_dict.keys()),
                lcu=lcu_selcted,
                by_operator=True,
                dataset_id=i,
                start_year=2008,
                end_year=2050,
                periodicity=Periodicity.Quarterly,
            )
            df_set_aux["item"] = item_name
            emp_lst.append(df_set_aux)
        df_set = pd.concat(emp_lst)
        df_set["year_quarter"] = df_set["year"].astype(str) + "Q" + df_set["quarter"].astype(str)
        st.subheader(f"{data_set_name_selected} - {'LCU' if not lcu_selcted else 'USD'} - {country_id_list_selected}")
        df_filter = df_set[df_set["country_code"].isin(country_id_list_selected)].sort_values(
            by=[
                "country_code",
                "item",
                "year",
                "quarter",
                "operator_id",
            ]
        )
        st.dataframe(df_filter, use_container_width=True)
        st.dataframe(
            df_filter.pivot_table(
                index=[
                    "item",
                    "country_code",
                    "operator_id",
                    "name",
                ],
                columns="year_quarter",
                values="value",
            ),
            use_container_width=True,
        )


with tab_spectrum_data:
    tn_op_lst = st.selectbox(
        "Select operator",
        list(operator_dict.values()),
        index=0,
        format_func=lambda x: list(operator_dict.keys())[list(operator_dict.values()).index(x)],
        key="tn_op_lst",
    )
    start_year, end_year = st.slider("Select period", 2011, 2031, (2008, 2031), 1)
    tab_spend, tab_annual_fee, tab_capex, tab_commitment, tab_ir_web, tab_start_expiries = st.tabs(
        ["Spend", "Annual fee", "Capex", "Commitment", "Investor relations web report", "Start/expiry"]
    )

    with tab_spend:
        metric_spend = st.selectbox(
            "Select metric",
            [QueryMetric.VAL_NOK, QueryMetric.VAL_LCU],
            index=0,
            format_func=lambda x: x.name[-3:],
            key="metric_spend",
        )

        spend_annual_fee_creator(metric_spend, FinanceKPIs.SPECTRUM_PAYMENT, start_year, end_year, key="spend")
    with tab_annual_fee:
        metric_annual_fee = st.selectbox(
            "Select metric",
            [QueryMetric.VAL_NOK, QueryMetric.VAL_LCU],
            index=1,
            format_func=lambda x: x.name[-3:],
            key="metric_annual_fee",
        )
        spend_annual_fee_creator(
            metric_annual_fee, FinanceKPIs.SPECTRUM_ANNUAL_FEE, start_year, end_year, key="annual_fee"
        )
    with tab_capex:
        metric_capex = st.selectbox(
            "Select metric",
            [QueryMetric.VAL_NOK, QueryMetric.VAL_LCU],
            index=1,
            format_func=lambda x: x.name[-3:],
            key="metric_capex",
        )
        spend_annual_fee_creator(metric_capex, FinanceKPIs.SPECTRUM_CAPEX, start_year, end_year, key="capex")
    with tab_commitment:
        metric_commit = st.selectbox(
            "Select metric",
            [QueryMetric.VAL_NOK, QueryMetric.VAL_LCU],
            index=1,
            format_func=lambda x: x.name[-3:],
            key="metric_commit",
        )
        spend_annual_fee_creator(metric_commit, FinanceKPIs.SPECTRUM_COMMITMENT, start_year, end_year, key="commitment")
    with tab_ir_web:
        metric_IR_report = st.selectbox(
            "Select metric",
            [QueryMetric.VAL_NOK, QueryMetric.VAL_LCU],
            index=1,
            format_func=lambda x: x.name[-3:],
            key="metric_IR_report",
        )
        df_ir_report = spend_annual_fee_creator(
            metric_IR_report, FinanceKPIs.SPECTRUM_COMMITMENT, 2008, 2050, key="ir_report"
        ).reset_index()
        df_ir_report = df_ir_report[df_ir_report["status"] == "committed"][
            [
                "country_name",
                "name",
                "reporting_currency_id",
                "status",
                "start_date",
                "stop_date",
                "band",
                "bandwidth",
                "Total",
            ]
        ].sort_values(by=["country_name", "name", "band", "stop_date", "start_date"])
        df_ir_report["Total"] = df_ir_report["Total"].round(0)
        df_ir_report[["start_date", "stop_date"]] = df_ir_report[["start_date", "stop_date"]].astype(int)
        df_ir_report = df_ir_report.set_index(
            [
                "country_name",
                "name",
                "reporting_currency_id",
                "status",
                "start_date",
                "stop_date",
                "band",
                "bandwidth",
            ]
        )

        st.write("Investor relations web report")
        st.dataframe(df_ir_report.style.format("{:,.0f}"), use_container_width=True, height=35 * len(df_ir_report) + 38)
    with tab_start_expiries:
        start_exp_df = start_expiry_table_creator(
            operator_list=tn_op_lst,
            metric=QueryMetric.VAL_LCU,
            periodicity=Periodicity.Annual,
            include_forecast=True,
            include_historic=True,
            detailed_outputs=True,
            financial_measure=FinanceKPIs.SPECTRUM_ANNUAL_FEE,
            start_year=start_year,
            end_year=end_year,
            extrapolation_fx_calc_date=None,
        )
        start_exp_df["start_date"] = start_exp_df["start_date"].dt.date
        start_exp_df["stop_date"] = start_exp_df["stop_date"].dt.date

        start_exp_df_tmp = (
            start_exp_df.drop(
                columns=[
                    "value",
                    "year",
                    "reporting_currency_id",
                ]
            )
            .drop_duplicates()
            .sort_values(by=["country_name", "name", "band", "stop_date"])
        )
        subhearder_ope_country_list = list(
            (start_exp_df_tmp["name"].astype(str) + "-" + start_exp_df_tmp["country_name"].astype(str)).unique()
        )
        st.subheader(f"Start and expiry dates: {subhearder_ope_country_list}")
        max_yr = st.slider("Select year", 2024, 2060, 2030, step=1)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Expiry: {2024}- {max_yr}")
            with st.expander("Expiry, operator by operator ", expanded=False):
                today = dt.datetime.today().date()
                start_exp_df_adj = start_exp_df_tmp[
                    start_exp_df_tmp["stop_date"].between(today, dt.datetime(max_yr, 12, 31).date())
                ]

                for o in tn_op_lst:
                    op_unique_bands = start_exp_df_adj[start_exp_df_adj["operator_id"] == o]["band"].unique()
                    if len(op_unique_bands) == 0:
                        continue
                    else:
                        operator_name_tmp = start_exp_df_adj[start_exp_df_adj["operator_id"] == o]["name"].unique()[0]
                    st.subheader(operator_name_tmp)
                    for b in op_unique_bands:
                        op_band_df = start_exp_df_adj[
                            (start_exp_df_adj["operator_id"] == o) & (start_exp_df_adj["band"] == b)
                        ]
                        st.subheader(f"{b} ({operator_name_tmp})")
                        st.dataframe(
                            op_band_df,
                            hide_index=True,
                            height=35 * len(op_band_df) + 38,
                        )
                    st.divider()

            start_stop_grp_df = (
                start_exp_df_adj.groupby(
                    [
                        "country_name",
                        "band",
                        "start_date",
                        "stop_date",
                    ]
                )
                .agg({"bandwidth": "sum"})
                .reset_index()
            ).sort_values(by=["country_name", "band", "stop_date", "start_date"])
            unique_bands = start_stop_grp_df["band"].unique()
            for b in unique_bands:
                display_df = start_stop_grp_df[start_stop_grp_df["band"] == b]
                st.subheader(f"{b} ({display_df['country_name'].unique()})")
                st.dataframe(display_df, hide_index=True, height=35 * len(display_df) + 38)
        with col2:
            st.subheader(f"Start: {2024}- {max_yr}")
            with st.expander("Start, operator by operator ", expanded=False):
                today = dt.datetime.today().date()
                start_exp_df_adj = start_exp_df_tmp[
                    start_exp_df_tmp["start_date"].between(today, dt.datetime(max_yr, 12, 31).date())
                ]

                for o in tn_op_lst:
                    op_unique_bands = start_exp_df_adj[start_exp_df_adj["operator_id"] == o]["band"].unique()
                    if len(op_unique_bands) == 0:
                        continue
                    else:
                        operator_name_tmp = start_exp_df_adj[start_exp_df_adj["operator_id"] == o]["name"].unique()[0]
                    st.subheader(operator_name_tmp)
                    for b in op_unique_bands:
                        op_band_df = start_exp_df_adj[
                            (start_exp_df_adj["operator_id"] == o) & (start_exp_df_adj["band"] == b)
                        ]
                        st.subheader(f"{b} ({operator_name_tmp})")
                        st.dataframe(
                            op_band_df,
                            hide_index=True,
                            height=35 * len(op_band_df) + 38,
                        )
                    st.divider()

            start_stop_grp_df = (
                start_exp_df_adj.groupby(
                    [
                        "country_name",
                        "band",
                        "start_date",
                        "stop_date",
                    ]
                )
                .agg({"bandwidth": "sum"})
                .reset_index()
            ).sort_values(by=["country_name", "band", "stop_date", "start_date"])
            unique_bands = start_stop_grp_df["band"].unique()
            for b in unique_bands:
                display_df = start_stop_grp_df[start_stop_grp_df["band"] == b]
                st.subheader(f"{b} ({display_df['country_name'].unique()})")
                st.dataframe(display_df, hide_index=True, height=35 * len(display_df) + 38)

# with tab_fiber:
#     comp_yr = list(range(2021, 2024)) + [np.nan]
#     year_lst = [2022, 2023, 2024]
#     segments_options = [np.nan, "SDU", "MDU"]
#     pub_lst = []
#     unpub_lst = []
#     pub_compl_yr = st.selectbox("Select completed year published", [None] + comp_yr, index=0, key="pub_compl_yr")
#    unpub_compl_yr = st.selectbox("Select completed year unpublished", [None] + comp_yr, index=1, key="unpub_compl_yr")
#     pub_segment = st.selectbox("Select segment published", [None] + segments_options, index=0, key="pub_segment")
#    unpub_segment = st.selectbox("Select segment unpublished", [None] + segments_options, index=2, key="unpub_segment")

#     @st.cache_data
#     def revenue_data(year, api):
#         return get_projects_revenue(Periodicity.Monthly, year, api)

#     for y in year_lst:
#         pub_rev_tmp = revenue_data(y, 1)[
#             [
#                 "date",
#                 "PROJECT_ID",
#                 "completed_date",
#                 "tot_rev_ex_vat",
#                 "rec_rev_ex_vat",
#                 "non_rec_rev_ex_vat",
#                 "numb_subs",
#                 "binding_share",
#             ]
#         ]
#         unpub_rev_tmp = revenue_data(y, 2)[
#             [
#                 "date",
#                 "PROJECT_ID",
#                 "completed_date",
#                 "tot_rev_ex_vat",
#                 "rec_rev_ex_vat",
#                 "non_rec_rev_ex_vat",
#                 "numb_subs",
#                 "binding_share",
#             ]
#         ]
#         unpub_lst.append(unpub_rev_tmp)
#         pub_lst.append(pub_rev_tmp)

#     pub_rev = pd.concat(pub_lst)
#     unpub_rev = pd.concat(unpub_lst)

#     pub_rev["year"] = pub_rev["date"].dt.year
#     unpub_rev["year"] = unpub_rev["date"].dt.year

#     pub_rev["month"] = pub_rev["date"].dt.month
#     unpub_rev["month"] = unpub_rev["date"].dt.month

#     pub_rev["completed_yr"] = pub_rev["completed_date"].dt.year
#     unpub_rev["completed_yr"] = unpub_rev["completed_date"].dt.year

#     pub_proj_lst = list(pub_rev["PROJECT_ID"].unique())
#     unpub_proj_lst = list(unpub_rev["PROJECT_ID"].unique())

#     proj_df_pub = get_project_costs(pub_proj_lst, 1)
#     proj_df_unpub = get_project_costs(unpub_proj_lst, 2)

#     proj_cost_merged = proj_df_pub.merge(proj_df_unpub, on="PROJECT_ID", how="outer", suffixes=("_pub", "_unpub"))
#     proj_cost_merged["completed_yr_pub"] = proj_cost_merged["completed_date_pub"].dt.year
#     proj_cost_merged["completed_yr_unpub"] = proj_cost_merged["completed_date_unpub"].dt.year

#     proj_cost_merged.to_excel("proj_cost_merged.xlsx", index=False)

#     proj_df_pub = proj_df_pub.drop(columns=["completed_date"])
#     proj_df_unpub = proj_df_unpub.drop(columns=["completed_date"])

#     pub_rev_cost = (
#       pub_rev.merge(proj_df_pub, left_on="PROJECT_ID", right_on="PROJECT_ID", how="left").fillna(np.nan).reset_index()
#     )
#     unpub_rev_cost = unpub_rev.merge(
#         proj_df_unpub,
#         left_on="PROJECT_ID",
#         right_on="PROJECT_ID",
#         how="left",
#     ).reset_index()
#     comp_yr_filter = [2021, 2022, 2023, 2024]
#     comp_yr_filter = [2017, 2018, 2019, 2020]
#     pub_unpub_rev_cost = pub_rev_cost[pub_rev_cost["completed_yr"].isin(comp_yr_filter)].merge(
#         unpub_rev_cost[unpub_rev_cost["completed_yr"].isin(comp_yr_filter)],
#         on=["PROJECT_ID", "year", "month"],
#         how="outer",
#         suffixes=("_pub", "_unpub"),
#     )
#     pub_unpub_rev_cost["revenue_delta"] = (
#         pub_unpub_rev_cost["tot_rev_ex_vat_pub"] - pub_unpub_rev_cost["tot_rev_ex_vat_unpub"]
#     )

#     pub_unpub_rev_cost.to_excel("pub_unpub_rev_cost.xlsx", index=False)

#     pub_rev_grp = (
#         (
#             pub_rev_cost.groupby(["completed_yr", "year", "month"]).agg(
#                 {
#                     "tot_rev_ex_vat": "sum",
#                     "rec_rev_ex_vat": "sum",
#                     "non_rec_rev_ex_vat": "sum",
#                     "numb_subs": "sum",
#                     "binding_share": "mean",
#                 }
#             )
#         )
#         .fillna(np.nan)
#         .reset_index()
#     )

#     unpub_rev_grp = (
#         unpub_rev_cost.groupby(["completed_yr", "year", "month"]).agg(
#             {
#                 "tot_rev_ex_vat": "sum",
#                 "rec_rev_ex_vat": "sum",
#                 "non_rec_rev_ex_vat": "sum",
#                 "numb_subs": "sum",
#                 "binding_share": "mean",
#             }
#         )
#     ).reset_index()

#     df_rev_delta = pub_rev_cost.merge(
#         unpub_rev_cost,
#         on=[
#             "year",
#             "month",
#             "PROJECT_ID",
#         ],
#         how="outer",
#         suffixes=("_pub", "_unpub"),
#     ).reset_index()

#     df_rev_delta["revenue_delta"] = df_rev_delta["tot_rev_ex_vat_pub"] - df_rev_delta["tot_rev_ex_vat_unpub"]

#     df_rev_delta_display = (
#         df_rev_delta[
#             (df_rev_delta["completed_yr_pub"].isin(comp_yr if pub_compl_yr is None else [pub_compl_yr]))
#             & (df_rev_delta["completed_yr_unpub"].isin(comp_yr if unpub_compl_yr is None else [unpub_compl_yr]))
#             & (
#                 df_rev_delta["PROJECT_AGREEMENT_TYPE_pub"].isin(
#                     segments_options if pub_segment is None else [pub_segment]
#                 )
#             )
#             & (
#                 df_rev_delta["PROJECT_AGREEMENT_TYPE_unpub"].isin(
#                     segments_options if unpub_segment is None else [unpub_segment]
#                 )
#             )
#         ]
#         .groupby(["year", "month"])
#         .agg(
#             {
#                 "revenue_delta": "sum",
#                 "tot_rev_ex_vat_pub": "sum",
#                 "rec_rev_ex_vat_pub": "sum",
#                 "non_rec_rev_ex_vat_pub": "sum",
#                 "numb_subs_pub": "sum",
#                 "binding_share_pub": "mean",
#                 "tot_rev_ex_vat_unpub": "sum",
#                 "rec_rev_ex_vat_unpub": "sum",
#                 "non_rec_rev_ex_vat_unpub": "sum",
#                 "numb_subs_unpub": "sum",
#                 "binding_share_unpub": "mean",
#             }
#         )
#     ).reset_index()
#     df_rev_delta_display["year_month"] = (
#         df_rev_delta_display["year"].astype(str) + "-" + df_rev_delta_display["month"].astype(str)
#     )
#     st.dataframe(df_rev_delta_display)

#     fig = px.line(
#         df_rev_delta_display,
#         x="year_month",
#         y="revenue_delta",
#         title="Revenue delta",
#     )
#     st.write("Revenue delta")

# st.write("Revenue delta")
# st.plotly_chart(fig, use_container_width=True)
