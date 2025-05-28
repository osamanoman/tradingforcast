from dash import html, dcc
import dash_bootstrap_components as dbc
from modules.utils import yf_tickers as Tickers
from os import environ


def format_ticker(ticker):
    return f"{ticker[1:]}" if ticker[0] == "^" else ticker


def serve_layout():
    tickers_list = (environ.get("TICKERS") or "^SPX,^NDX,^RUT,GLD,SPY,QQQ").strip().split(",")
    tickers = Tickers(tickers_list)
    ticker_info = {ticker: tickers.tickers[ticker].info for ticker in tickers_list}
    
    # Create the layout components
    layout = dbc.Container(
        [
            dcc.Store(
                id="theme-store",
                storage_type="local",
                data=[dbc.themes.FLATLY, dbc.themes.DARKLY],
            ),
            dbc.Navbar(
                dbc.Container([
                    dbc.NavbarBrand("MMEC", className="ms-2"),
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
                className="mb-4",
            ),
            dbc.Row(
                children=[
                    dbc.Button(
                        html.I(className="bi bi-info"),
                        color="info",
                        outline=True,
                        class_name="d-flex align-items-center justify-content-center",
                        style={
                            "width": "30px",
                            "height": "22px",
                            "fontSize": "1.1rem",
                        },
                        id="info-btn",
                    ),
                    dbc.Popover(
                        dbc.PopoverBody(
                            children=[
                                "G|Flows, or Greek Flows, measures market risks that \
                                can affect option prices. ",
                                html.Br(),
                                html.Span(
                                    "Monday-Friday: 15-minute updates from 9:00am-4:30pm ET (CBOE delayed data)",
                                    className="fst-italic",
                                ),
                            ]
                        ),
                        style={"fontSize": "12px"},
                        target="info-btn",
                        trigger="hover",
                        placement="left",
                    ),
                ],
                class_name="d-flex justify-content-between align-items-center mx-auto my-2",
            ),
            dbc.Row(
                html.Div(
                    html.H2("GAMMA"),
                    className="mx-auto d-flex justify-content-center",
                )
            ),
            dcc.Interval(
                id="interval", interval=1000 * 3 * 1, n_intervals=0
            ),
            dcc.Store(id="refresh", storage_type="local"),
            dbc.Row(
                dcc.Dropdown(
                    options=[
                        {"label": "S&P 500 INDEX (SPX)", "value": "spx"},
                        {"label": "NASDAQ 100 (NDX)", "value": "ndx"},
                        {"label": "Russell 2000 (RUT)", "value": "rut"},
                        {"label": "SPDR Gold Shares (GLD)", "value": "gld"},
                        {"label": "SPDR S&P 500 ETF (SPY)", "value": "spy"},
                        {"label": "Invesco QQQ Trust (QQQ)", "value": "qqq"},
                        {"label": "Apple (AAPL)", "value": "aapl"},
                        {"label": "Tesla (TSLA)", "value": "tsla"},
                        {"label": "Google (GOOG)", "value": "goog"},
                        {"label": "Microsoft (MSFT)", "value": "msft"},
                        {"label": "Amazon (AMZN)", "value": "amzn"},
                        {"label": "Meta (META)", "value": "meta"},
                        {"label": "Nvidia (NVDA)", "value": "nvda"},
                        {"label": "AMD (AMD)", "value": "amd"},
                        {"label": "Netflix (NFLX)", "value": "nflx"},
                        {"label": "Alibaba (BABA)", "value": "baba"},
                    ],
                    id="tabs",
                    placeholder="Select Symbol",
                    searchable=False,
                    clearable=False,
                    className="d-flex h-100 border border-primary btn-outline-primary align-items-center",
                    persistence=True,
                    persistence_type="local",
                ),
                class_name="px-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(html.H4("Expirations"), className="mx-auto"),
                            dbc.ButtonGroup(
                                children=[
                                    html.Div(
                                        dcc.Dropdown(
                                            options=[
                                                {
                                                    "label": "Monthly",
                                                    "value": "monthly-btn",
                                                },
                                                {
                                                    "label": "OPEX",
                                                    "value": "opex-btn",
                                                },
                                                {
                                                    "label": "0DTE",
                                                    "value": "0dte-btn",
                                                },
                                            ],
                                            id="monthly-options",
                                            placeholder="Monthly",
                                            searchable=False,
                                            clearable=False,
                                            className="d-flex h-100 border border-primary btn-outline-primary align-items-center",
                                            persistence=True,
                                            persistence_type="local",
                                        ),
                                        className="w-50",
                                    ),
                                    dbc.Button(
                                        "All",
                                        id="all-btn",
                                        color="primary",
                                        active=False,
                                        outline=True,
                                        n_clicks=0,
                                    ),
                                ],
                                id="exp-btns",
                            ),
                        ],
                        class_name="d-flex flex-column mt-2",
                    ),
                    dbc.Col(
                        [
                            html.Div(html.H4("Greeks"), className="mx-auto"),
                            dcc.Store(id="greek-value", storage_type="local"),
                            dcc.Dropdown(
                                options=[
                                    {"label": "Delta", "value": "delta-btn"},
                                    {"label": "Gamma", "value": "gamma-btn"},
                                    {"label": "Vanna", "value": "vanna-btn"},
                                    {"label": "Charm", "value": "charm-btn"},
                                ],
                                id="greek-dropdown",
                                placeholder="Select Greek",
                                searchable=False,
                                clearable=False,
                                className="d-flex h-100 border border-primary btn-outline-primary align-items-center",
                                persistence=True,
                                persistence_type="local",
                            ),
                        ],
                        class_name="d-flex flex-column mt-2",
                    ),
                ],
            ),
            dcc.Store(id="exp-value", storage_type="local"),
            dbc.Row(
                dcc.Dropdown(
                    placeholder="",
                    clearable=False,
                    searchable=False,
                    id="live-dropdown",
                    persistence=True,
                    persistence_type="local",
                ),
                class_name="mt-2",
            ),
            dbc.Row(
                dbc.Col(
                    children=[
                        html.Div(
                            [
                                dbc.DropdownMenu(
                                    label=html.I(className="bi bi-download"),
                                    color="primary",
                                    children=[
                                        dbc.DropdownMenuItem(
                                            "Export chart data", id="btn-chart-data"
                                        ),
                                        dbc.DropdownMenuItem(
                                            "Export significant points",
                                            id="btn-sig-points",
                                        ),
                                    ],
                                    size="sm",
                                ),
                                dcc.Download(id="export-df-csv"),
                            ],
                            className="me-auto",
                        ),
                        html.Div(
                            children=[
                                dbc.Label(className="bi bi-sun-fill my-auto"),
                                dbc.Switch(
                                    id="switch",
                                    className="d-flex justify-content-center mx-1",
                                    persistence=True,
                                    persistence_type="local",
                                ),
                                dbc.Label(className="bi bi-moon-fill my-auto"),
                            ],
                            className="d-flex align-items-center me-4",
                            id="theme-btn-div",
                        ),
                        html.Div(
                            dbc.Pagination(
                                id="pagination",
                                active_page=1,
                                max_value=2,
                                size="sm",
                                class_name="mb-0 me-1",
                            ),
                            hidden=True,
                            id="pagination-div",
                        ),
                    ],
                    class_name="d-flex justify-content-end align-items-center",
                ),
                class_name="mt-2",
            ),
            dcc.Loading(
                id="loading-icon",
                children=[
                    dbc.Row(
                        dcc.Graph(
                            id="live-chart",
                            responsive=True,
                            style={
                                "display": "none"
                            },
                        ),
                        class_name="vw-100 vh-100 mt-0",
                    ),
                    dbc.Row(
                        dcc.Graph(
                            id="bs-breakdown-chart",
                            style={"height": "400px", "marginTop": "40px"},
                        ),
                        class_name="vw-100 vh-100 mt-0",
                    ),
                    dbc.Row(
                        html.Footer("* expirations up to monthly OPEX"),
                        class_name="float-end align-super",
                    ),
                ],
                type="default",
            ),
        ],
        class_name="vw-100 vh-100",
        fluid=True,
    )
    return layout

def serve_polygon_layout():
    """Layout for the Polygon Options page"""
    return dbc.Container([
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

def serve_options_flow_layout():
    """Layout for the Options Flow page"""
    return dbc.Container([
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
                html.H1("Indices Flow Analysis", className="text-center mb-2 fw-bold", style={"fontSize": "2.5rem", "color": "#f8f9fa", "letterSpacing": "1px"}),
                html.H5("Monitor and analyze real-time options flow for indices. Data updates every 5 minutes.", className="text-center mb-4", style={"color": "#b0b3b8", "fontWeight": 400}),
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
                            html.Span(id='flow-last-updated', style={'verticalAlign': 'middle', 'fontSize': '1rem', 'color': '#f8f9fa'}),
                            html.I(className='bi bi-info-circle ms-2', style={'color': '#bbb', 'verticalAlign': 'middle'}),
                        ], style={'marginBottom': '18px', 'marginLeft': '2px'})
                    ])
                ]),
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Indices Flow Data", className="fw-semibold mb-3", style={"color": "#f8f9fa"}),
                        dbc.Table(
                            id="flow-table",
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
            id="flow-interval",
            interval=60000,  # 1 minute
            n_intervals=0
        ),
        dcc.Store(id="flow-data-store"),
    ], fluid=True, style={"backgroundColor": "#181a1b", "minHeight": "100vh", "paddingTop": "30px", "paddingBottom": "30px"})

def serve_market_analysis_layout():
    """Layout for the Market Analysis page"""
    return dbc.Container([
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
