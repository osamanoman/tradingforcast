import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from dash import Dash, html, Input, Output, ctx, no_update, State, dash, dcc
from dash.dcc import send_data_frame
from dash.exceptions import PreventUpdate
from flask import Flask, session, redirect, url_for, request
from flask_caching import Cache
import pandas as pd
from modules.calc import get_options_data
from modules.ticker_dwn import dwn_data
from modules.layout import serve_layout, serve_polygon_layout, serve_options_flow_layout
from modules.utils import patch_yf
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import cron, combining
from datetime import timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from os import environ
from os import path
import textwrap
from pandas import DataFrame, concat
import os
import datetime
import threading
import numpy as np
import scipy.stats as st
import orjson
from pathlib import Path
import re
from functools import wraps
import json

load_dotenv()  # load environment variables from .env
patch_yf()  # Apply the patch

server = Flask(__name__)
app = Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.DARKLY,
        dbc.themes.FLATLY,
        dbc.icons.BOOTSTRAP,
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    title="MMEC",
    update_title=None,
    suppress_callback_exceptions=True,
)

# Set a secret key for session management
server.secret_key = environ.get('SECRET_KEY', 'your-secret-key-here')

# Cache configuration
cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "FileSystemCache",
        "CACHE_DIR": "cache",
        "CACHE_THRESHOLD": 150,
    },
)

cache.clear()

# Restore the original layout and routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/polygon_options':
        return serve_polygon_layout()
    elif pathname == '/options_flow':
        return serve_options_flow_layout()
    elif pathname == '/market_analysis':
        return serve_market_analysis_layout()
    else:
        return serve_layout()

@cache.memoize(timeout=60 * 15)  # cache charts for 15 min
def analyze_data(ticker, expir):
    try:
        # Analyze stored data of specified ticker and expiry
        # defaults: json format, timezone 'America/New_York'
        result = get_options_data(
            ticker,
            expir,
            is_json=True,  # False for CSV
            tz="America/New_York",
        )
        if not result:
            print(f"No data available for {ticker} {expir}")
            return (None,) * 16
        return result
    except Exception as e:
        print(f"Error analyzing data for {ticker} {expir}: {str(e)}")
        return (None,) * 16


def cache_data(ticker, expir):
    try:
        data = analyze_data(ticker, expir)
        if data[0] is None:  # Check if we got valid data
            print(f"Invalid data for {ticker} {expir}")
            return data
            
        if not cache.has(f"{ticker}_{expir}"):
            cache.set(  # for client/server sync
                f"{ticker}_{expir}",
                {
                    "ticker": ticker,
                    "expiration": expir,
                    "spot_price": data[4],
                    "monthly_options_dates": data[3],
                    "today_ddt": data[1],
                    "today_ddt_string": data[2],
                    "zero_delta": data[12],
                    "zero_gamma": data[13],
                },
            )
        return data
    except Exception as e:
        print(f"Error caching data for {ticker} {expir}: {str(e)}")
        return (None,) * 16


def sensor(select=None):
    try:
        # default: all tickers, json format
        dwn_data(select, is_json=True)  # False for CSV
        cache.clear()
        print("Data download completed successfully")
    except Exception as e:
        print(f"Error downloading data: {str(e)}")
        # Try to use existing data if download fails
        pass


def check_for_retry():
    tickers = cache.get("retry")
    if tickers:
        print("\nRedownloading data due to missing greek exposure...\n")
        sensor(select=tickers)





# schedule when to redownload data
sched = BackgroundScheduler(daemon=True)
sched.add_job(
    sensor,
    combining.OrTrigger(
        [
            cron.CronTrigger.from_crontab(
                "0,15,30,45 9-15 * * 0-4", timezone=ZoneInfo("America/New_York")
            ),
            cron.CronTrigger.from_crontab(
                "0,15,30 16 * * 0-4", timezone=ZoneInfo("America/New_York")
            ),
        ]
    ),
)
sched.add_job(
    check_for_retry,
    combining.OrTrigger(
        [
            cron.CronTrigger(
                day_of_week="0-4",
                hour="9-15",
                second="*/5",
                timezone=ZoneInfo("America/New_York"),
            ),
            cron.CronTrigger(
                day_of_week="0-4",
                hour="16",
                minute="0-30",
                second="*/5",
                timezone=ZoneInfo("America/New_York"),
            ),
        ]  # during the specified times, check every 5 seconds for a retry condition
    ),
)
sched.start()

app.clientside_callback(  # toggle light or dark theme
    """ 
    (themeToggle, theme) => {
        let themeLink = themeToggle ? theme[1] : theme[0]
        let kofiBtn = themeToggle ? "dark" : "light"
        let kofiLink = themeToggle ? "link-light" : "link-dark"
        let stylesheets = document.querySelectorAll(
            'link[rel=stylesheet][href^="https://cdn.jsdelivr"]'
        )
        // Update main theme
        stylesheets[1].href = themeLink
        // Update buffer after a short delay
        setTimeout(() => {stylesheets[0].href = themeLink;}, 100)
        return [kofiBtn, kofiLink]
    }
    """,
    [Output("kofi-btn", "color"), Output("kofi-link-color", "className")],
    [Input("switch", "value"), State("theme-store", "data")],
)


@app.callback(  # handle selected expiration
    Output("exp-value", "data"),
    Output("all-btn", "active"),
    Output("monthly-options", "value"),
    Input("monthly-options", "value"),
    Input("all-btn", "n_clicks"),
    State("exp-value", "data"),
)
def on_click(value, btn, expiration):
    if not ctx.triggered_id and expiration:
        value = f"{expiration}-btn"
    if ctx.triggered_id == "all-btn" or value == "all-btn":
        return "all", True, None
    else:
        button_map = {
            "monthly-btn": ("monthly", False, "monthly-btn"),
            "opex-btn": ("opex", False, "opex-btn"),
            "0dte-btn": ("0dte", False, "0dte-btn"),
        }
        return button_map.get(value, ("monthly", False, "monthly-btn"))


@app.callback(  # handle selected option greek
    Output("greek-value", "data"),
    Output("pagination", "active_page"),
    Output("live-dropdown", "options"),
    Output("live-dropdown", "value"),
    Input("greek-dropdown", "value"),
    Input("pagination", "active_page"),
    Input("live-dropdown", "value"),
    State("greek-value", "data"),
)
def on_click(greek_value, active_page, value, greek):
    if not ctx.triggered_id and greek:
        active_page, options, value = (
            greek["active_page"],
            greek["options"],
            greek["value"],
        )
    elif ctx.triggered_id == "live-dropdown":
        active_page, options = greek["active_page"], greek["options"]
    elif ctx.triggered_id == "pagination":
        options, value = greek["options"], greek["value"]
    else:
        button_map = {
            "delta-btn": (
                [
                    "Absolute Delta Exposure",
                    "Delta Exposure By Calls/Puts",
                    "Delta Exposure Profile",
                ],
                "Absolute Delta Exposure",
            ),
            "gamma-btn": (
                [
                    "Absolute Gamma Exposure",
                    "Gamma Exposure By Calls/Puts",
                    "Gamma Exposure Profile",
                ],
                "Absolute Gamma Exposure",
            ),
            "vanna-btn": (
                [
                    "Absolute Vanna Exposure",
                    "Implied Volatility Average",
                    "Vanna Exposure Profile",
                ],
                "Absolute Vanna Exposure",
            ),
            "charm-btn": (
                [
                    "Absolute Charm Exposure",
                    "Charm Exposure Profile",
                ],
                "Absolute Charm Exposure",
            ),
        }
        options, value = button_map.get(greek_value or "delta-btn", button_map["delta-btn"])

    greek = {
        "active_page": active_page,
        "options": options,
        "value": value,
    }

    return greek, active_page, options, value


@app.callback(  # handle refreshed data
    Output("refresh", "data"),
    Output("interval", "n_intervals"),
    Input("interval", "n_intervals"),
    State("tabs", "value"),
    State("exp-value", "data"),
    State("live-chart", "figure"),
)
def check_cache_key(n_intervals, stock, expiration, fig):
    if not stock:  # if no symbol is selected
        raise PreventUpdate
    data = cache.get(f"{stock.lower()}_{expiration}")
    if not data and stock and expiration:
        cache_data(stock.lower(), expiration)
    if (
        data
        and (fig and fig["data"])
        and (
            data["today_ddt_string"]
            and data["ticker"] == stock.lower()
            and data["ticker"].upper()
            in fig["layout"]["title"]["text"].replace("<br>", " ")
            and data["expiration"] == expiration
        )
        and (
            data["today_ddt_string"]
            not in fig["layout"]["title"]["text"].replace("<br>", " ")
            or (
                "shapes" in fig["layout"]
                and "name" in fig["layout"]["shapes"][-1]
                and data["spot_price"] != fig["layout"]["shapes"][-1]["x0"]
            )
        )
    ):  # refresh on current selection if client data differs from server cache
        return data, 0
    raise PreventUpdate


@app.callback(
    Output("export-df-csv", "data"),
    [
        Input("btn-chart-data", "n_clicks"),
        Input("btn-sig-points", "n_clicks"),
        Input("export-menu", "n_clicks"),
    ],
    State("tabs", "value"),
    State("exp-value", "data"),
    State("pagination", "active_page"),
    State("live-dropdown", "value"),
    State("live-chart", "figure"),
    prevent_initial_call=True,
)
def handle_export(btn1, btn2, menu, stock, expiration, active_page, value, fig):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    if not stock:
        raise PreventUpdate

    data = cache.get(f"{stock.lower()}_{expiration}")
    if not data or not data["today_ddt"] or not fig["data"]:
        raise PreventUpdate

    fig_data = fig["data"]

    if not fig_data[0]["y"]:
        raise PreventUpdate

    if expiration != "all":
        date_formats = {
            "monthly": data["monthly_options_dates"][0].strftime("%Y-%b"),
            "opex": data["monthly_options_dates"][1].strftime("%Y-%b-%d"),
            "0dte": data["monthly_options_dates"][0].strftime("%Y-%b-%d"),
        }
        exp_date = date_formats[expiration]
    else:
        exp_date = "All_Expirations"

    date_condition = active_page == 2 and not "Profile" in value
    prefix = "Strikes" if not date_condition else "Dates"
    formatted_date = str(data["today_ddt"]).replace(" ", "_")
    chart_name = value.replace(" ", "_")
    filename = f"{prefix}_{chart_name}_{exp_date}__{formatted_date}.csv"

    df_agg = DataFrame(
        data=zip(*[item["y"] for item in fig_data if item["y"]]),
        index=fig_data[0]["x"],
        columns=[item["name"] for item in fig_data if item["y"]],
    )
    df_agg.index.name = prefix

    if trigger == "btn-chart-data":
        return send_data_frame(
            df_agg.to_csv,
            f"{stock}_{filename}",
        )
    elif trigger == "btn-sig-points":
        significant_points = DataFrame(
            {
                f"Signif_{col.replace(' ', '_')}": concat(
                    [
                        df_agg.loc[df_agg[col] > 0, col].nlargest(5),
                        df_agg.loc[df_agg[col] < 0, col].nsmallest(5),
                    ]
                )
                for col in df_agg.columns
            }
        )
        if "Delta" in value:
            significant_points["Delta_Flip"] = data["zero_delta"]
        elif "Gamma" in value:
            significant_points["Gamma_Flip"] = data["zero_gamma"]
        return send_data_frame(
            significant_points.fillna(0).to_csv,
            f"{stock}_SigPoints_{filename}",
        )
    elif trigger == "export-menu":
        # Default to exporting chart data
        return send_data_frame(
            df_agg.to_csv,
            f"{stock}_{filename}",
        )

    raise PreventUpdate


@app.callback(  # handle chart display based on inputs
    Output("live-chart", "figure"),
    Output("live-chart", "style"),
    Output("pagination-div", "hidden"),
    Output("monthly-options", "options"),
    Input("live-dropdown", "value"),
    Input("tabs", "value"),
    Input("exp-value", "data"),
    Input("pagination", "active_page"),
    Input("refresh", "data"),
    Input("switch", "value"),
)
def update_live_chart(value, stock, expiration, active_page, refresh, toggle_dark):
    if not stock:  # if no symbol is selected
        return (
            go.Figure(layout={"title_text": "Please select a symbol"}),
            {},
            True,
            no_update,
        )
    (
        df,
        today_ddt,
        today_ddt_string,
        monthly_options_dates,
        spot_price,
        from_strike,
        to_strike,
        levels,
        totaldelta,
        totalgamma,
        totalvanna,
        totalcharm,
        zerodelta,
        zerogamma,
        call_ivs,
        put_ivs,
    ) = cache_data(stock.lower(), expiration)

    # chart theme and layout
    xaxis, yaxis = dict(
        gridcolor="lightgray", minor=dict(ticklen=5, tickcolor="#000", showgrid=True)
    ), dict(gridcolor="lightgray", minor=dict(tickcolor="#000"))
    layout = {
        "title_x": 0.5,
        "title_font_size": 12.5,
        "title_xref": "paper",
        "legend": dict(
            orientation="v",
            yanchor="top",
            xanchor="right",
            y=0.98,
            x=0.98,
            bgcolor="rgba(0,0,0,0.1)",
            font_size=10,
        ),
        "showlegend": True,
        "margin": dict(l=0, r=40),
        "xaxis": xaxis,
        "yaxis": yaxis,
        "dragmode": "pan",
    }
    if not toggle_dark:
        # light theme
        pio.templates["custom_template"] = pio.templates["seaborn"]
    else:
        # dark theme
        pio.templates["custom_template"] = pio.templates["plotly_dark"]
        for axis in [xaxis, yaxis]:
            axis["gridcolor"], axis["minor"]["tickcolor"] = "#373737", "#707070"
        layout["paper_bgcolor"] = "#222222"
        layout["plot_bgcolor"] = "rgba(40, 40, 50, 0.8)"
    pio.templates["custom_template"].update(layout=layout)
    pio.templates.default = "custom_template"

    if df is None:
        return (
            go.Figure(layout={"title_text": f"{stock} data unavailable, retry later"}),
            {},
            True,
            no_update,
        )

    retry_cache = cache.get("retry")
    if (
        df["total_delta"].sum() == 0
        and (not retry_cache or stock not in retry_cache)
        and (
            expiration not in ["0dte", "opex"]
            or (
                expiration == "0dte"
                and today_ddt < monthly_options_dates[0] + timedelta(minutes=15)
            )
            or (
                expiration == "opex"
                and today_ddt < monthly_options_dates[1] + timedelta(minutes=15)
            )
        )
    ):
        # if data hasn't expired and total delta exposure is 0,
        # set a 'retry' for the scheduler to catch
        retry_cache = retry_cache or []
        retry_cache.append(stock)
        cache.set("retry", retry_cache)

    date_condition = active_page == 2 and not "Profile" in value
    if not date_condition:
        df_agg = df.groupby(["strike_price"]).sum(numeric_only=True)
        df_agg = df_agg[from_strike:to_strike]  # filter for relevance
        call_ivs, put_ivs = call_ivs["strike"], put_ivs["strike"]
    else:  # use dates
        df_agg = df.groupby(["expiration_date"]).sum(numeric_only=True)
        # df_agg = df_agg[: today_ddt + timedelta(weeks=52)] # filter for relevance
        call_ivs, put_ivs = call_ivs["exp"], put_ivs["exp"]

    date_formats = {
        "monthly": monthly_options_dates[0].strftime("%Y %b"),
        "opex": monthly_options_dates[1].strftime("%Y %b %d"),
        "0dte": monthly_options_dates[0].strftime("%Y %b %d"),
    }
    monthly_options = [  # provide monthly option labels
        {
            "label": monthly_options_dates[0].strftime("%Y %B"),
            "value": "monthly-btn",
        },
        {
            "label": html.Div(
                children=[
                    monthly_options_dates[1].strftime("%Y %B %d"),
                    html.Span("*", className="align-super"),
                ],
                className="d-flex align-items-center",
            ),
            "value": "opex-btn",
        },
        {
            "label": monthly_options_dates[0].strftime("%Y %B %d"),
            "value": "0dte-btn",
        },
    ]
    legend_title = (
        date_formats[expiration] if expiration != "all" else "All Expirations"
    )

    strikes = df_agg.index.to_numpy()

    is_profile_or_volatility = "Profile" in value or "Average" in value
    name = value.split()[1] if "Absolute" in value else value.split()[0]

    name_to_vals = {
        "Delta": (
            f"per 1% {stock} Move",
            f"{name} Exposure (price / 1% move)",
            zerodelta,
        ),
        "Gamma": (
            f"per 1% {stock} Move",
            f"{name} Exposure (delta / 1% move)",
            zerogamma,
        ),
        "Vanna": (
            f"per 1% {stock} IV Move",
            f"{name} Exposure (delta / 1% IV move)",
            0,
        ),
        "Charm": (
            f"a day til {stock} Expiry",
            f"{name} Exposure (delta / day til expiry)",
            0,
        ),
        "Implied": ("", "Implied Volatility (IV) Average", 0),
    }

    description, y_title, zeroflip = name_to_vals[name]
    yaxis.update(title_text=y_title)
    scale = 10**9

    if "Absolute" in value:
        fig = go.Figure(
            data=[
                go.Bar(
                    name=name + " Exposure",
                    x=strikes,
                    y=df_agg[f"total_{name.lower()}"].to_numpy(),
                    marker=dict(
                        line=dict(
                            width=0.25,
                            color=("#2B5078" if not toggle_dark else "#8795FA"),
                        ),
                    ),
                )
            ]
        )
    elif "Calls/Puts" in value:
        fig = go.Figure(
            data=[
                go.Bar(
                    name="Call " + name,
                    x=strikes,
                    y=df_agg[f"call_{name[:1].lower()}ex"].to_numpy() / scale,
                    marker=dict(
                        line=dict(
                            width=0.25,
                            color=("#2B5078" if not toggle_dark else "#8795FA"),
                        ),
                    ),
                ),
                go.Bar(
                    name="Put " + name,
                    x=strikes,
                    y=df_agg[f"put_{name[:1].lower()}ex"].to_numpy() / scale,
                    marker=dict(
                        line=dict(
                            width=0.25,
                            color=("#9B5C30" if not toggle_dark else "#F5765B"),
                        ),
                    ),
                ),
            ]
        )

    if not is_profile_or_volatility:
        split_title = textwrap.wrap(
            f"Total {name}: $"
            + str("{:,.2f}".format(df[f"total_{name.lower()}"].sum() * scale))
            + f" {description}, {today_ddt_string}",
            width=50,
        )
        fig.update_layout(  # bar chart layout
            title_text="<br>".join(split_title),
            legend_title_text=legend_title,
            xaxis=xaxis,
            yaxis=yaxis,
            barmode="relative",
            modebar_remove=["autoscale", "lasso2d"],
        )
    if is_profile_or_volatility:
        fig = make_subplots(rows=1, cols=1)
        if not date_condition and name != "Implied":  # chart profiles
            split_title = textwrap.wrap(
                f"{stock} {name} Exposure Profile, {today_ddt_string}", width=50
            )
            name_to_vals = {
                "Delta": (
                    totaldelta["all"],
                    totaldelta["ex_next"],
                    totaldelta["ex_fri"],
                ),
                "Gamma": (
                    totalgamma["all"],
                    totalgamma["ex_next"],
                    totalgamma["ex_fri"],
                ),
                "Vanna": (
                    totalvanna["all"],
                    totalvanna["ex_next"],
                    totalvanna["ex_fri"],
                ),
                "Charm": (
                    totalcharm["all"],
                    totalcharm["ex_next"],
                    totalcharm["ex_fri"],
                ),
            }
            all_ex, ex_next, ex_fri = name_to_vals[name]
            fig.add_trace(go.Scatter(x=levels, y=all_ex, name="All Expiries"))
            fig.add_trace(go.Scatter(x=levels, y=ex_next, name="Next Expiry"))
            fig.add_trace(go.Scatter(x=levels, y=ex_fri, name="Next Monthly Expiry"))
            # show - &/or + areas of exposure depending on condition
            if name == "Charm" or name == "Vanna":
                all_ex_min, all_ex_max = all_ex.min(), all_ex.max()
                min_n = [
                    all_ex_min,
                    ex_fri.min() if ex_fri.size != 0 else all_ex_min,
                    ex_next.min() if ex_next.size != 0 else all_ex_min,
                ]
                max_n = [
                    all_ex_max,
                    ex_fri.max() if ex_fri.size != 0 else all_ex_max,
                    ex_next.max() if ex_next.size != 0 else all_ex_max,
                ]
                min_n.sort()
                max_n.sort()
                if min_n[0] < 0:
                    fig.add_hrect(
                        y0=0,
                        y1=min_n[0] * 1.5,
                        fillcolor="red",
                        opacity=0.1,
                        line_width=0,
                    )
                if max_n[2] > 0:
                    fig.add_hrect(
                        y0=0,
                        y1=max_n[2] * 1.5,
                        fillcolor="green",
                        opacity=0.1,
                        line_width=0,
                    )
                fig.add_hline(
                    y=0,
                    line_width=0,
                    name=name + " Flip",
                    annotation_text=name + " Flip",
                    annotation_position="top left",
                )
            # greek has a - to + flip
            elif zeroflip > 0:
                fig.add_vline(
                    x=zeroflip,
                    line_color="dimgray",
                    line_width=1,
                    name=name + " Flip",
                    annotation_text=name + " Flip: " + str("{:,.0f}".format(zeroflip)),
                    annotation_position="top left",
                )
                fig.add_vrect(
                    x0=from_strike,
                    x1=zeroflip,
                    fillcolor="red",
                    opacity=0.1,
                    line_width=0,
                )
                fig.add_vrect(
                    x0=zeroflip,
                    x1=to_strike,
                    fillcolor="green",
                    opacity=0.1,
                    line_width=0,
                )
            # flip unknown, assume - dominance
            elif all_ex[0] < 0:
                fig.add_vrect(
                    x0=from_strike,
                    x1=to_strike,
                    fillcolor="red",
                    opacity=0.1,
                    line_width=0,
                )
            # flip unknown, assume + dominance
            elif all_ex[0] > 0:
                fig.add_vrect(
                    x0=from_strike,
                    x1=to_strike,
                    fillcolor="green",
                    opacity=0.1,
                    line_width=0,
                )
        elif name == "Implied":  # in IV section, chart put/call IV averages
            fig.add_trace(
                go.Scatter(
                    x=strikes,
                    y=put_ivs * 100,
                    name="Put IV",
                    fill="tozeroy",
                    line_color="#C44E52",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=strikes,
                    y=call_ivs * 100,
                    name="Call IV",
                    fill="tozeroy",
                    line_color="#32A3A3",
                )
            )
            split_title = textwrap.wrap(
                f"{stock} IV Average, {today_ddt_string}", width=50
            )
        fig.add_hline(
            y=0,
            line_width=1,
            line_color="dimgray",
        )
        fig.update_layout(  # scatter chart layout
            title_text="<br>".join(split_title),
            legend_title_text=legend_title,
            xaxis=xaxis,
            yaxis=yaxis,
            modebar_remove=["autoscale"],
        )

    fig.update_xaxes(
        title="Strike" if not date_condition else "Date",
        showgrid=True,
        range=(
            [spot_price * 0.9, spot_price * 1.1]
            if not date_condition
            else (
                [
                    strikes[0] - timedelta(seconds=0.0625),
                    strikes[0] + timedelta(seconds=0.0625),
                ]
                if len(strikes) == 1
                else [today_ddt, today_ddt + timedelta(days=31)]
            )
        ),
        gridwidth=1,
        rangeslider=dict(visible=True),
    )
    fig.update_yaxes(
        showgrid=True,
        fixedrange=True,
        minor_ticks="inside",
        gridwidth=1,
    )

    if not date_condition:
        fig.add_vline(
            x=spot_price,
            line_color="#707070",
            line_width=1,
            line_dash="dash",
            name=stock + " Spot",
            annotation_text="Last: " + str("{:,.2f}".format(spot_price)),
            annotation_position="top",
        )

    is_pagination_hidden = "Profile" in value

    return fig, {}, is_pagination_hidden, monthly_options


@app.callback(
    Output("info-btn", "children", allow_duplicate=True),
    [Input("about-menu", "n_clicks"), Input("docs-menu", "n_clicks"), Input("support-menu", "n_clicks")],
    prevent_initial_call=True,
)
def handle_help_menu(about_clicks, docs_clicks, support_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "about-menu":
        return html.Div([
            html.H4("About G|Flows"),
            html.P("G|Flows is a powerful options flow analysis tool that helps traders track and analyze options market activity."),
            html.P("Version: 1.0.0"),
      
    
    raise PreventUpdate


# Add modals for help and settings
app.layout = html.Div([
    app.layout,
    dbc.Modal([
        dbc.ModalHeader("Settings"),
        dbc.ModalBody([
            dbc.Form([
                dbc.Label("Theme"),
                dbc.Select(
                    id="theme-select",
                    options=[
                        {"label": "Light", "value": "light"},
                        {"label": "Dark", "value": "dark"},
                    ],
                    value="dark",
                ),
            ]),
            dbc.Form([
                dbc.Label("Update Interval (seconds)"),
                dbc.Input(
                    id="interval-input",
                    type="number",
                    min=1,
                    max=60,
                    value=3,
                ),
            ]),
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-settings", className="ms-auto", n_clicks=0)
        ),
    ], id="settings-modal"),
    
    dbc.Modal([
        dbc.ModalHeader(id="help-modal-header"),
        dbc.ModalBody(id="help-modal-body"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-help", className="ms-auto", n_clicks=0)
        ),
    ], id="help-modal"),
])


@app.callback(
    Output("settings-modal", "is_open"),
    [
        # Input("settings-menu", "n_clicks"),  # Commented out because the component is missing
        Input("close-settings", "n_clicks")
    ],
    [State("settings-modal", "is_open")],
)
def toggle_settings_modal(n2, is_open):
    if n2:
        return not is_open
    return is_open


@app.callback(
    Output("interval", "interval"),
    Input("interval-input", "value"),
)
def update_interval(value):
    if value:
        return value * 1000  # convert to milliseconds
    raise PreventUpdate


@app.callback(
    [Output("help-modal", "is_open"),
     Output("help-modal-header", "children"),
     Output("help-modal-body", "children")],
    [Input("about-menu", "n_clicks"),
     Input("docs-menu", "n_clicks"),
     Input("support-menu", "n_clicks"),
     Input("close-help", "n_clicks")],
    [State("help-modal", "is_open")],
    prevent_initial_call=True,
)
def toggle_help_modal(about_clicks, docs_clicks, support_clicks, close_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "close-help":
        return False, "", ""
    
    if button_id == "about-menu":
        return True, "About G|Flows", html.Div([
            html.P("G|Flows is a powerful options flow analysis tool that helps traders track and analyze options market activity."),
            html.P("Version: 1.0.0"),
        ])
   
    
    raise PreventUpdate


@app.callback(
    Output('polygon-table', 'children'),
    [Input('polygon-interval', 'n_intervals')],
    prevent_initial_call=True
)
def update_polygon_table(n_intervals):
    output_path = os.path.expanduser("~/options_data.csv")
    if not os.path.exists(output_path):
        return html.Div("No data available")
    
    try:
      
        # Extract base symbol from ticker if needed
        if 'ticker' in df.columns:
            df['ticker'] = df['ticker'].apply(lambda x: x.split(':')[1].split('2')[0] if isinstance(x, str) and x.startswith('O:') else x)
        
        # Ensure bid_size and ask_size are included and sum to volume
        if 'bid_size' in df.columns and 'ask_size' in df.columns and 'volume' in df.columns:
            # Scale bid/ask sizes to match volume while maintaining their ratio
            total_size = df['bid_size'] + df['ask_size']
            valid_ratio = total_size > 0
            df.loc[valid_ratio, 'bid_size'] = (df.loc[valid_ratio, 'volume'] * df.loc[valid_ratio, 'bid_size'] / total_size).round().astype(int)
            df.loc[valid_ratio, 'ask_size'] = df.loc[valid_ratio, 'volume'] - df.loc[valid_ratio, 'bid_size']
            
            # For rows without valid bid/ask sizes, distribute based on contract type
            no_ratio = ~valid_ratio
            df.loc[no_ratio & (df['contract_type'] == 'call'), 'bid_size'] = (df.loc[no_ratio & (df['contract_type'] == 'call'), 'volume'] * 0.6).round().astype(int)
            df.loc[no_ratio & (df['contract_type'] == 'put'), 'bid_size'] = (df.loc[no_ratio & (df['contract_type'] == 'put'), 'volume'] * 0.4).round().astype(int)
            df.loc[no_ratio, 'ask_size'] = df.loc[no_ratio, 'volume'] - df.loc[no_ratio, 'bid_size']
        
        # Format numeric columns
        numeric_cols = ['volume', 'open_interest', 'volume_oi_ratio', 'moneyness', 'underlying_price', 'bid_size', 'ask_size']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').round(2)
        
        # Create header and body
        header = html.Thead(html.Tr([html.Th(col.replace('_', ' ').title()) for col in df.columns]))
        body = html.Tbody([
            html.Tr([html.Td(str(df.iloc[i][col])) for col in df.columns])
            for i in range(len(df))
        ])
        
        return [header, body]
    except Exception as e:
        print(f"Error updating polygon table: {e}")
        return html.Div("Error updating data")


@app.callback(
    Output('flow-table', 'children'),
    [
        Input('flow-interval', 'n_intervals'),
        Input('asset-type-dropdown', 'value'),
        Input('ticker-filter', 'value'),
        Input('premium-filter', 'value'),
        Input('quantity-filter', 'value'),
        Input('volume-filter', 'value'),
    ],
    prevent_initial_call=True
)
def update_flow_table(n_intervals, asset_type, ticker_filter, premium_filter, quantity_filter, volume_filter):
    # Determine which JSON file to read based on the selected asset type
    json_path = None
    if asset_type == 'indices':
        json_path = r"C:/Users/pc/Downloads/gflows-main(1)/gflows-main/data/json"
    elif asset_type == 'etfs':
        json_path = r"C:/Users/pc/Downloads/gflows-main(1)/gflows-main/data/json"
    # Add conditions for 'stocks' or other types if needed in the future

    if json_path is None or not os.path.exists(json_path):
        return html.Div("No data available")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        if not data:
            return html.Div("No data available")
        import pandas as pd
        df = pd.DataFrame(data)
        # Apply filters only if input is not None or empty
        if ticker_filter:
            df = df[df['Ticker'].str.contains(ticker_filter, case=False, na=False)]
        if premium_filter is not None and premium_filter != '':
            try:
                premium_filter_float = float(premium_filter)
                # Remove '$' and ',' from 'Premium' column before filtering
                df['Premium_numeric'] = df['Premium'].astype(str).str.replace('$','').str.replace(',','').astype(float)
                df = df[df['Premium_numeric'] >= premium_filter_float]
                df = df.drop(columns=['Premium_numeric'])
            except ValueError:
                pass # Ignore invalid premium filter input
        if quantity_filter is not None and quantity_filter != '':
            try:
                quantity_filter_int = int(quantity_filter)
                # Remove ',' from 'Quantity' column before filtering
                df['Quantity_numeric'] = df['Quantity'].astype(str).str.replace(',','').astype(int)
                df = df[df['Quantity_numeric'] >= quantity_filter_int]
                df = df.drop(columns=['Quantity_numeric'])
            except ValueError:
                pass # Ignore invalid quantity filter input
        if volume_filter is not None and volume_filter != '':
            try:
                volume_filter_int = int(volume_filter)
                # Remove ',' from 'Volume' column before filtering
                df['Volume_numeric'] = df['Volume'].astype(str).str.replace(',','').astype(int)
                df = df[df['Volume_numeric'] >= volume_filter_int]
                df = df.drop(columns=['Volume_numeric'])
            except ValueError:
                pass # Ignore invalid volume filter input
        # Columns to display (in order)
        display_cols = [
            ('Timestamp', 'Timestamp'),
            ('Ticker', 'Ticker'),
            ('Contract', 'Contract'),
            ('Premium', 'Premium'),
            ('Price', 'Price'),
            ('Quantity', 'Quantity'),
            ('Volume', 'Volume'),
            ('Open Interest', 'Open Interest'),
            ('Side', 'Side'),
            ('Days to Exp', 'Days to Exp'),
        ]
        def safe_display(val, col):
            if col == 'Contract':
                val_str = str(val)
                parts = val_str.split()
                if len(parts) == 3:
                    strike, contract_type, expiry_date = parts
                    type_style = {}
                    if contract_type.upper() == 'CALL':
                        type_style = {'color': 'limegreen', 'fontWeight': 'bold'}
                    elif contract_type.upper() == 'PUT':
                        type_style = {'color': 'red', 'fontWeight': 'bold'}
                    return html.Div([
                        html.Span(f"{strike} "),
                        html.Span(f"{contract_type}", style=type_style),
                        html.Span(f" {expiry_date}")
                    ])
                return val_str # return original string if parsing fails
            if col in ['Premium']:
                try:
                    v = str(val).replace('$','').replace(',','')
                    return f"{float(v):,.0f}" if v not in [None, '', 'N/A'] else 'N/A'
                except:
                    return val
            if col in ['Price']:
                try:
                    return f"{float(val):,.2f}" if val not in [None, '', 'N/A'] else 'N/A'
                except:
                    return val
            if col in ['Quantity', 'Volume', 'Open Interest', 'Days to Exp']:
                try:
                    return f"{int(float(val))}" if val not in [None, '', 'N/A'] else 'N/A'
                except:
                    return val
            return val if val not in [None, '', 'N/A'] else 'N/A'
        def get_cell_style(col, value):
            base_style = {
                'padding': '8px',
                'textAlign': 'right' if col in ['Premium','Price','Quantity','Volume','Open Interest','Days to Exp'] else 'left',
                'fontWeight': 500 if col == 'Side' else 400,
                'borderBottom': 'none' # Remove bottom border for cells
            }
            
            
        
        header = html.Thead(html.Tr([
            html.Th(label, style={'textAlign': 'center'}) for _, label in display_cols
        ]))
        body = html.Tbody([
            html.Tr(
                [
                    html.Td(
                        safe_display(df.iloc[i][col], label),
                        style={
                            **get_cell_style(label, df.iloc[i][col]),
                            'backgroundColor': '#23272b' if i % 2 == 0 else '#3f3d3d' # Alternating row color
                        }
                    ) for col, label in display_cols
                ],
                style={'borderBottom': 'none'} # Ensure no border on the row itself
            ) for i in range(len(df))
        ])
        return [header, body]
    except Exception as e:
        return html.Div(f"Error loading data: {str(e)}")


@app.callback(
    Output('analysis-table', 'children'),
    [
        Input('analysis-interval', 'n_intervals'),
        Input('analysis-ticker-filter', 'value'),
        Input('analysis-premium-filter', 'value'),
        Input('analysis-quantity-filter', 'value'),
        Input('analysis-volume-filter', 'value'),
    ],
    prevent_initial_call=True
)
def update_analysis_table(n_intervals, ticker_filter, premium_filter, quantity_filter, volume_filter):
    json_path = r"C:/Users/pc/Downloads/gflows-main(1)/gflows-main/data/json/market_analysis_data.json"
    if not os.path.exists(json_path):
        return html.Div("No data available")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        if not data:
            return html.Div("No data available")
        import pandas as pd
        df = pd.DataFrame(data)
        
        # Apply filters only if input is not None or empty
        if ticker_filter:
            df = df[df['Ticker'].str.contains(ticker_filter, case=False, na=False)]
        if premium_filter is not None and premium_filter != '':
            try:
                premium_filter_float = float(premium_filter)
                # Remove '$' and ',' from 'Premium' column before filtering
                df['Premium_numeric'] = df['Premium'].astype(str).str.replace('$','').str.replace(',','').astype(float)
                df = df[df['Premium_numeric'] >= premium_filter_float]
                df = df.drop(columns=['Premium_numeric'])
            except ValueError:
                pass # Ignore invalid premium filter input
        if quantity_filter is not None and quantity_filter != '':
            try:
                quantity_filter_int = int(quantity_filter)
                # Remove ',' from 'Quantity' column before filtering
                df['Quantity_numeric'] = df['Quantity'].astype(str).str.replace(',','').astype(int)
                df = df[df['Quantity_numeric'] >= quantity_filter_int]
                df = df.drop(columns=['Quantity_numeric'])
            except ValueError:
                pass # Ignore invalid quantity filter input
        if volume_filter is not None and volume_filter != '':
            try:
                volume_filter_int = int(volume_filter)
                # Remove ',' from 'Volume' column before filtering
                df['Volume_numeric'] = df['Volume'].astype(str).str.replace(',','').astype(int)
                df = df[df['Volume_numeric'] >= volume_filter_int]
                df = df.drop(columns=['Volume_numeric'])
            except ValueError:
                pass # Ignore invalid volume filter input
        
        # Columns to display (in order)
        display_cols = [
            ('Timestamp', 'Timestamp'),
            ('Ticker', 'Ticker'),
            ('Contract', 'Contract'),
            ('Premium', 'Premium'),
            ('Price', 'Price'),
            ('Quantity', 'Quantity'),
            ('Volume', 'Volume'),
            ('Open Interest', 'Open Interest'),
            ('Side', 'Side'),
            ('Days to Exp', 'Days to Exp'),
        ]
        
        def safe_display(val, col):
            if col == 'Contract':
                val_str = str(val)
                parts = val_str.split()
                if len(parts) == 3:
                    strike, contract_type, expiry_date = parts
                    type_style = {}
                    if contract_type.upper() == 'CALL':
                        type_style = {'color': 'limegreen', 'fontWeight': 'bold'}
                    elif contract_type.upper() == 'PUT':
                        type_style = {'color': 'red', 'fontWeight': 'bold'}
                    return html.Div([
                        html.Span(f"{strike} "),
                        html.Span(f"{contract_type}", style=type_style),
                        html.Span(f" {expiry_date}")
                    ])
                return val_str # return original string if parsing fails
            if col in ['Premium']:
                try:
                    v = str(val).replace('$','').replace(',','')
                    return f"{float(v):,.0f}" if v not in [None, '', 'N/A'] else 'N/A'
                except:
                    return val
            if col in ['Price']:
                try:
                    return f"{float(val):,.2f}" if val not in [None, '', 'N/A'] else 'N/A'
                except:
                    return val
            if col in ['Quantity', 'Volume', 'Open Interest', 'Days to Exp']:
                try:
                    return f"{int(float(val))}" if val not in [None, '', 'N/A'] else 'N/A'
                except:
                    return val
            return val if val not in [None, '', 'N/A'] else 'N/A'
        
        def get_cell_style(col, value):
            base_style = {
                'padding': '8px',
                'textAlign': 'right' if col in ['Premium','Price','Quantity','Volume','Open Interest','Days to Exp'] else 'left',
                'fontWeight': 500 if col == 'Side' else 400,
                'borderBottom': 'none' # Remove bottom border for cells
            }
            if col == 'Side':
                v = str(value).lower()
                if 'buyer' in v:
                    return {**base_style, 'color': 'limegreen'}
                elif 'seller' in v:
                    return {**base_style, 'color': 'red'}
                elif 'ask' in v:
                    return {**base_style, 'color': 'limegreen'}
                elif 'bid' in v:
                    return {**base_style, 'color': 'red'}
            return base_style
        
        header = html.Thead(html.Tr([
            html.Th(label, style={'textAlign': 'center'}) for _, label in display_cols
        ]))
        body = html.Tbody([
            html.Tr(
                [
                    html.Td(
                        safe_display(df.iloc[i][col], label),
                        style={
                            **get_cell_style(label, df.iloc[i][col]),
                            'backgroundColor': '#23272b' if i % 2 == 0 else '#3f3d3d' # Alternating row color
                        }
                    ) for col, label in display_cols
                ],
                style={'borderBottom': 'none'} # Ensure no border on the row itself
            ) for i in range(len(df))
        ])
        return [header, body]
    except Exception as e:
        return html.Div(f"Error loading data: {str(e)}")


@app.callback(
    Output('polygon-last-updated', 'children'),
    [Input('polygon-interval', 'n_intervals')],
    prevent_initial_call=True
)
def update_polygon_last_updated(n_intervals):
    output_path = os.path.expanduser("~/options_data.csv")
    if not os.path.exists(output_path):
        return "Last updated: N/A"
    mtime = os.path.getmtime(output_path)
    dt = datetime.datetime.fromtimestamp(mtime)
    # Format as: Feb 10, 4:15:50 PM ET
    formatted = dt.strftime('%b %d, %-I:%M:%S %p ET')
    return f"Last updated: {formatted}"


@app.callback(
    Output('analysis-last-updated', 'children'),
    [Input('analysis-interval', 'n_intervals')],
    prevent_initial_call=True
)
def update_analysis_last_updated(n_intervals):
    output_path = r"C:/Users/pc/Downloads/gflows-main(1)/gflows-main/data/json/market_analysis_data.json"
    if not os.path.exists(output_path):
        return "Last updated: N/A"
    mtime = os.path.getmtime(output_path)
    dt = datetime.datetime.fromtimestamp(mtime)
    # Format as: Feb 10, 4:15:50 PM ET
    formatted = dt.strftime('%b %d, %I:%M:%S %p ET').lstrip('0')
    return f"Last updated: {formatted}"


@app.callback(
    Output('flow-last-updated', 'children'),
    [Input('flow-interval', 'n_intervals')],
    prevent_initial_call=True
)
def update_flow_last_updated(n_intervals):
    output_path = r"C:/Users/pc/Downloads/gflows-main(1)/gflows-main/data/csv/options_flow_data.csv"
    if not os.path.exists(output_path):
        return "Last updated: N/A"
    mtime = os.path.getmtime(output_path)
    dt = datetime.datetime.fromtimestamp(mtime)
    formatted = dt.strftime('%b %d, %I:%M:%S %p ET').lstrip('0')
    return f"Last updated: {formatted}"


def serve_polygon_layout():
    """Layout for the Polygon Options page"""
    return dbc.Container([
        # Menu Bar
        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand("G|Flows", className="ms-2 fw-bold", style={"fontSize": "2rem", "letterSpacing": "2px"}),
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Home", href="/")),
                    dbc.NavItem(dbc.NavLink("FLOW Stocks", href="/polygon-options")),
                    dbc.NavItem(dbc.NavLink("FLOW Indices", href="/options-flow")),
                    dbc.NavItem(dbc.NavLink("FLOW ETFs", href="/market-analysis")),
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem("About", id="about-menu"),
                            dbc.DropdownMenuItem("Documentation", id="docs-menu"),
                            dbc.DropdownMenuItem("Support", id="support-menu"),
                        ],
                        label="Help",
                        nav=True,
                    ),
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem("Export Data", id="export-menu"),
                            dbc.DropdownMenuItem("Settings", id="settings-menu"),
                        ],
                        label="Tools",
                        nav=True,
                    ),
                ], className="ms-auto"),
            ]),
            color="primary",
            dark=True,
            className="mb-4 shadow-sm rounded",
            style={"fontSize": "1.1rem"}
        ),
        dbc.Row([
            dbc.Col([
                html.H1("Stocks Flow Analysis", className="text-center mb-2 fw-bold", style={"fontSize": "2.5rem", "color": "#f8f9fa", "letterSpacing": "1px"}),
                html.H5("Monitor and analyze real-time options flow for stocks. Data updates every 5 minutes.", className="text-center mb-4", style={"color": "#b0b3b8", "fontWeight": 400}),
                # Last Updated Bar
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Span(
                                style={
                                    'display': 'inline-block',
                                    'width': '14px',
                                    'height': '14px',
                                    'backgroundColor': '#21d07a',
                                    'borderRadius': '50%',
                                    'marginRight': '8px',
                                    'verticalAlign': 'middle',
                                }
                            ),
                            html.Span(id='polygon-last-updated', style={'verticalAlign': 'middle', 'fontSize': '1rem', 'color': '#f8f9fa'}),
                            html.I(className='bi bi-info-circle ms-2', style={'color': '#bbb', 'verticalAlign': 'middle'}),
                        ], style={'marginBottom': '18px', 'marginLeft': '2px'})
                    ])
                ]),
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Stocks Flow Data", className="fw-semibold mb-3", style={"color": "#f8f9fa"}),
                        dbc.Table(
                            id="polygon-table",
                            bordered=True,
                            hover=True,
                            responsive=True,
                            striped=True,
                            size="sm",
                            className="table-fixed",
                            style={
                                "maxHeight": "70vh",
                                "overflowY": "auto",
                                "fontSize": "0.8rem",
                                "backgroundColor": "#23272b",
                                "color": "#f8f9fa",
                                "borderRadius": "12px",
                                "border": "1px solid #343a40",
                                "boxShadow": "0 2px 12px rgba(0,0,0,0.15)",
                                "marginBottom": "0"
                            }
                        ),
                    ])
                ], className="shadow-lg border-0", style={"backgroundColor": "#181a1b", "borderRadius": "16px", "padding": "2rem 1.5rem", "margin": "0 auto", "maxWidth": "98vw"}),
            ], width=12, className="d-flex flex-column align-items-center justify-content-center"),
        ]),
        dcc.Interval(
            id="polygon-interval",
            interval=300000,  # 5 minutes
            n_intervals=0
        ),
        dcc.Store(id="polygon-data-store"),
    ], fluid=True, style={"backgroundColor": "#181a1b", "minHeight": "100vh", "paddingTop": "30px", "paddingBottom": "30px"})


def serve_market_analysis_layout():
    """Layout for the Market Analysis page"""
    return dbc.Container([
        # Menu Bar
        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand("G|Flows", className="ms-2 fw-bold", style={"fontSize": "2rem", "letterSpacing": "2px"}),
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Home", href="/")),
                    dbc.NavItem(dbc.NavLink("FLOW Stocks", href="/polygon-options")),
                    dbc.NavItem(dbc.NavLink("FLOW Indices", href="/options-flow")),
                    dbc.NavItem(dbc.NavLink("FLOW ETFs", href="/market-analysis")),
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem("About", id="about-menu"),
                            dbc.DropdownMenuItem("Documentation", id="docs-menu"),
                            dbc.DropdownMenuItem("Support", id="support-menu"),
                        ],
                        label="Help",
                        nav=True,
                    ),
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem("Export Data", id="export-menu"),
                            dbc.DropdownMenuItem("Settings", id="settings-menu"),
                        ],
                        label="Tools",
                        nav=True,
                    ),
                ], className="ms-auto"),
            ]),
            color="primary",
            dark=True,
            className="mb-4 shadow-sm rounded",
            style={"fontSize": "1.1rem"}
        ),
        dbc.Row([
            dbc.Col([
                html.H1("ETFs Flow Analysis", className="text-center mb-2 fw-bold", style={"fontSize": "2.5rem", "color": "#f8f9fa", "letterSpacing": "1px"}),
                html.H5("Monitor and analyze real-time options flow for ETFs. Data updates every 5 minutes.", className="text-center mb-4", style={"color": "#b0b3b8", "fontWeight": 400}),
                # Last Updated Bar
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Span(
                                style={
                                    'display': 'inline-block',
                                    'width': '14px',
                                    'height': '14px',
                                    'backgroundColor': '#21d07a',
                                    'borderRadius': '50%',
                                    'marginRight': '8px',
                                    'verticalAlign': 'middle',
                                }
                            ),
                            html.Span(id='analysis-last-updated', style={'verticalAlign': 'middle', 'fontSize': '1rem', 'color': '#f8f9fa'}),
                            html.I(className='bi bi-info-circle ms-2', style={'color': '#bbb', 'verticalAlign': 'middle'}),
                        ], style={'marginBottom': '18px', 'marginLeft': '2px'})
                    ])
                ]),
                dbc.Card([
                    dbc.CardBody([
                        html.H4("ETFs Flow Data", className="fw-semibold mb-3", style={"color": "#f8f9fa"}),
                        dbc.Table(
                            id="analysis-table",
                            bordered=True,
                            hover=True,
                            responsive=True,
                            striped=True,
                            size="sm",
                            className="table-fixed",
                            style={
                                "maxHeight": "70vh",
                                "overflowY": "auto",
                                "fontSize": "0.8rem",
                                "backgroundColor": "#23272b",
                                "color": "#f8f9fa",
                                "borderRadius": "12px",
                                "border": "1px solid #343a40",
                                "boxShadow": "0 2px 12px rgba(0,0,0,0.15)",
                                "marginBottom": "0"
                            }
                        ),
                    ])
                ], className="shadow-lg border-0", style={"backgroundColor": "#181a1b", "borderRadius": "16px", "padding": "2rem 1.5rem", "margin": "0 auto", "maxWidth": "98vw"}),
            ], width=12, className="d-flex flex-column align-items-center justify-content-center"),
        ]),
        dcc.Interval(
            id="analysis-interval",
            interval=300000,  # 5 minutes
            n_intervals=0
        ),
        dcc.Store(id="analysis-data-store"),
    ], fluid=True, style={"backgroundColor": "#181a1b", "minHeight": "100vh", "paddingTop": "30px", "paddingBottom": "30px"})


@app.callback(
    Output('bs-breakdown-chart', 'figure'),
    [
        Input('tabs', 'value'),
        Input('exp-value', 'data'),
        Input('switch', 'value'),
    ]
)
def update_bs_breakdown_chart(tabs, exp_value, toggle_dark):
    if isinstance(tabs, str):
        stock = tabs
    else:
        stock = "spx"  # fallback default
    expiration = exp_value if isinstance(exp_value, str) else "monthly-btn"
    df, *_ = cache_data(stock.lower(), expiration)
    if df is None or df.empty:
        return go.Figure(layout={"title_text": "No data"})
    # Use call/put open interest columns
    if all(col in df.columns for col in ['strike_price', 'call_open_int', 'put_open_int']):
        grouped = df.groupby('strike_price').agg({
            'call_open_int': 'sum',
            'put_open_int': 'sum'
        }).reset_index()
        x = grouped['strike_price']
        y_call = grouped['call_open_int']
        y_put = grouped['put_open_int']
    else:
        print("bs-breakdown-chart: DataFrame columns:", df.columns.tolist())
        return go.Figure(layout={"title_text": "Missing call/put open interest columns"})
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x,
        y=y_call,
        name='Call OI',
        marker_color='green',
    ))
    fig.add_trace(go.Bar(
        x=x,
        y=y_put,
        name='Put OI',
        marker_color='red',
    ))
    fig.update_layout(
        barmode='group',
        title=f"{stock.upper()} Option Breakdown",
        xaxis_title=f"{stock.upper()} Strike",
        yaxis_title="Open Interest",
        template='plotly_dark' if toggle_dark else 'plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port="8050")
