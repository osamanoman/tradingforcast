# -*- coding: utf-8 -*-
"""
Script pour récupérer et afficher le flux d'options (Options Flow) depuis Polygon.io.
"""

import os
from datetime import datetime
from polygon.rest import RESTClient
import re
import pandas as pd
import json
import time
import random
import concurrent.futures

# --- Configuration ---
API_KEY = "M563eKqwZduqpb0G5PUlaqpAKpoGnmVi"
UNDERLYING_TICKERS = ["TSLA", "NVDA", "AAPL", "AMD", "PDD", "AMZN", "MSTR", "PLTR", "GOOG", "X", "MARA", "CRVW", "DJT", "SMCI", "UNH", "QBTS", "HOOD", "BBAI", "SOFI", "GOOGLE", "SOUN", "NVTS", "RGTI", "META", "INTC", "MSFT", "RIOT", "OKLO", "NIO", "AAL", "RKLB", "EOSE", "CCJ", "RIVN", "HIMS", "BABA", "XYZ", "IQ", "LLY", "COIN", "SMR", "TEM", "UBER", "BAC", "AVGO", "CLF", "NFLX", "PFE", "SNOW", "MU", "IONQ", "KHC", "MRVL", "ACHR", "CLSK", "FUBO", "JD", "QUBT", "F", "ASTS", "NKE", "WOLF", "CRWD", "WMT", "MRNA", "RDDT", "CORZ", "APLD", "PONY", "CVNA", "LCID", "AI", "CCL", "U", "PEP", "RUN", "OKTA", "TGT", "CRM", "ARM", "TEVA", "CELH", "XOM", "BYND", "LYFT", "XPEV", "SNAP", "FCX", "NNE", "YEXT", "DIS", "M", "DECA", "VRT", "HPE", "INFA", "NVCR", "PCT", "NBEV", "LVS", "PYPL", "ORCL", "C", "CPN", "JPM", "SHOP", "JBLU", "APP", "DELL", "GE", "KO", "SBUX", "ETSY", "VST", "CVX", "ENPH", "AG", "NEM", "FSLR", "DKS", "T", "RXRX", "PRTA", "OXY", "PANW", "QCOM", "HAL", "CNK", "NCLH", "NXE", "TMC", "RILY", "AFRM", "WRBY", "DAL", "FLR", "VZ", "NU", "CMC", "UAL", "CVS", "ANF", "PLUG", "MRK", "PENN", "KSS", "ZIM", "DKNG", "BIDU", "HTZ", "URBN", "OSCR", "WFC", "ELF", "AAP", "ET", "DOW", "SBSW", "BRK.B", "MO", "TWC", "UPS", "B", "UL", "NVAX", "COST", "DANA", "PATH", "TTD", "GM", "VALE", "PSQ", "VFC", "TLRD", "LAZR", "MRVL", "COMA", "AGNC", "KTOS", "BB", "W", "ATUS", "GEV", "GS", "NEE", "LIMN", "CEG"]  # List of tickers to process
MIN_PREMIUM_THRESHOLD = 0  # $0 minimum premium
MIN_VOLUME = 100  # Minimum volume threshold
MIN_OPEN_INTEREST = 100  # Minimum open interest threshold
MAX_DAYS_TO_EXPIRATION = 200  # Maximum days until expiration
LIMIT = 50

# Configuration for random processing and delay
TICKER_PROCESS_DELAY_SECONDS = 5 # Delay between processing each ticker

# Create output directory if it doesn't exist
OUTPUT_DIR = os.path.join("gflows-main", "data", "json")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Define the consistent output file path
OUTPUT_JSON_FILE = os.path.join(OUTPUT_DIR, "polygon_options_data.json")

def parse_options_ticker(ticker):
    """Parse an options ticker to extract details."""
    match = re.match(r"O:([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d+)", ticker)
    if match:
        underlying, year_short, month, day, option_type, strike = match.groups()
        year = 2000 + int(year_short)  # Assuming 20xx years
        expiry_date = f"{year}-{month}-{day}"
        strike_price = float(strike) / 1000  # Convert to actual strike price
        option_type_str = "PUT" if option_type == "P" else "CALL"
        return expiry_date, strike_price, option_type_str
    return None, None, None

def format_timestamp(ts_nanos):
    """Convertit un timestamp en nanosecondes en une chaîne de caractères lisible."""
    if ts_nanos is None:
        return "N/A"
    ts_seconds = ts_nanos / 1_000_000_000
    dt_object = datetime.fromtimestamp(ts_seconds)
    return dt_object.strftime("%Y-%m-%d %I:%M:%S %p")

def get_options_flow(ticker, api_key, limit, min_premium):
    """Récupère les données de flux d'options depuis l'API Polygon.io."""
    client = RESTClient(api_key)
    all_flow_data = []
    contract_count = 0
    current_date = datetime.now()

    try:
        print(f"\nFetching options chain for {ticker}...")
        # Get options chain
        contracts = client.list_snapshot_options_chain(
            underlying_asset=ticker
        )
        
        print(f"Processing contracts for {ticker}...")
        
        for contract in contracts:
            contract_count += 1
            try:
                option_ticker = contract.details.ticker
                # print(f"\nProcessing contract {contract_count}: {option_ticker}") # Keep this line for debugging if needed
                
                # Parse expiration date and contract details
                expiry_date, strike_price, option_type = parse_options_ticker(option_ticker)
                if expiry_date:
                    exp_date = datetime.strptime(expiry_date, "%Y-%m-%d")
                    days_to_exp = (exp_date - current_date).days
                    
                    # Filter by expiration date
                    if days_to_exp > MAX_DAYS_TO_EXPIRATION:
                        # print(f"Skipping: Expiration too far ({days_to_exp} days)") # Keep for debugging if needed
                        continue
                else:
                    # print(f"Could not parse expiration date from {option_ticker}") # Keep for debugging if needed
                    continue

                # Get last trade
                trades = client.list_trades(option_ticker, limit=1)
                if not trades:
                    # print(f"No trades found for {option_ticker}") # Keep for debugging if needed
                    continue

                last_trade = next(trades, None)
                if not last_trade:
                    continue

                price = last_trade.price
                size = last_trade.size
                premium = price * size * 100  # Standard 100 shares per contract

                # Filter by minimum premium
                if premium < min_premium:
                    continue

                # Get contract details
                spot_price = getattr(contract.underlying_asset, 'price', 0) if hasattr(contract, 'underlying_asset') else 0
                volume = getattr(contract.day, 'volume', 0) if hasattr(contract, 'day') else 0
                open_interest = getattr(contract, 'open_interest', 0)
                conditions = getattr(last_trade, 'conditions', [])

                # Filter by minimum volume
                if volume < MIN_VOLUME:
                    # print(f"Skipping: Volume ({volume}) below minimum threshold ({MIN_VOLUME})") # Keep for debugging
                    continue

                # Filter by minimum open interest
                if open_interest < MIN_OPEN_INTEREST:
                    # print(f"Skipping: Open Interest ({open_interest}) below minimum threshold ({MIN_OPEN_INTEREST})") # Keep for debugging
                    continue

                # Determine side (Bid/Ask)
                quote = getattr(contract, 'last_quote', None)
                side = "-"
                if quote:
                    bid = getattr(quote, 'bid', 0)
                    ask = getattr(quote, 'ask', 0)
                    if price <= bid:
                        side = "Bid"
                    elif price >= ask:
                        side = "Ask"

                # Format conditions
                condition_str = ','.join(map(str, conditions)) if conditions else "-"

                # Create readable contract name
                contract_name = f"{strike_price:.0f} {option_type} {expiry_date}"

                flow_data = {
                    "Timestamp": format_timestamp(last_trade.sip_timestamp),
                    "Ticker": ticker,
                    "Contract": contract_name,
                    "Premium": premium,
                    "Price": price,
                    "Spot": spot_price,
                    "Quantity": size,
                    "Volume": volume,
                    "Open Interest": open_interest,
                    "Side": side,
                    "Condition": condition_str,
                    "Days to Exp": days_to_exp
                }
                all_flow_data.append(flow_data)
                # print(f"Added data for {contract_name}") # Keep for debugging

            except Exception as e:
                print(f"Error processing contract {option_ticker}: {str(e)}")
                continue

        print(f"Processed {contract_count} contracts for {ticker}")
        return all_flow_data

    except Exception as e:
        print(f"Error fetching options data for {ticker}: {str(e)}")
        return None

def print_flow_table(flow_data):
    """Affiche les données de flux dans un tableau formaté."""
    if not flow_data:
        print("Aucune donnée de flux d'options trouvée ou erreur lors de la récupération.")
        return

    # Définir les en-têtes du tableau
    headers = ["Timestamp", "Ticker", "Contract", "Premium", "Price", "Spot", "Quantity", "Volume", "Open Interest", "Side", "Condition", "Days to Exp"]

    # Déterminer la largeur maximale pour chaque colonne
    col_widths = {header: len(header) for header in headers}
    for row in flow_data:
        for header in headers:
            # Formater les nombres pour la lisibilité
            value = row[header]
            if value is None:
                value_str = "N/A"
            elif header == "Premium":
                value_str = f"${value:,.0f}"
            elif header in ["Price", "Spot"]:
                value_str = f"{value:.2f}"
            elif header in ["Quantity", "Volume", "Open Interest", "Days to Exp"]:
                value_str = f"{value:,}"
            else:
                value_str = str(value)

            col_widths[header] = max(col_widths[header], len(value_str))
            row[header] = value_str

    # Créer la ligne d'en-tête
    header_line = " | ".join(f"{header:<{col_widths[header]}}" for header in headers)
    separator_line = "-+- ".join("-" * col_widths[header] for header in headers)

    print(header_line)
    print(separator_line)

    # Afficher les lignes de données
    for row in flow_data:
        row_line = " | ".join(f"{row[header]:<{col_widths[header]}}" for header in headers)
        print(row_line)

if __name__ == "__main__":
    print(f"Starting periodic and random options flow data collection for {', '.join(UNDERLYING_TICKERS)}")
    print(f"Filters: Premium > ${MIN_PREMIUM_THRESHOLD:,}, Volume > {MIN_VOLUME:,}, Open Interest > {MIN_OPEN_INTEREST:,}, Max Days to Expiration: {MAX_DAYS_TO_EXPIRATION}")
    
    try:
        while True: # Keep processing indefinitely
            all_accumulated_results = [] # Accumulate results for this cycle
            
            print(f"\nStarting new processing cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit tasks for each ticker
                future_to_ticker = {
                    executor.submit(get_options_flow, ticker, API_KEY, LIMIT, MIN_PREMIUM_THRESHOLD): ticker
                    for ticker in UNDERLYING_TICKERS
                }
                
                for future in concurrent.futures.as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        flow_results = future.result()
                        if flow_results:
                            all_accumulated_results.extend(flow_results)
                            print(f"Added {len(flow_results)} results for {ticker}. Total accumulated: {len(all_accumulated_results)}")
                        else:
                            print(f"No flow results found for {ticker}.")
                    except Exception as exc:
                        print(f'{ticker} generated an exception: {exc}')

            # After processing all tickers in the shuffled list
            if all_accumulated_results:
                # Get today's date in YYYY-MM-DD format for filtering
                today_date_str = datetime.now().strftime("%Y-%m-%d")

                # Filter results for the same date as today
                filtered_results = [
                    flow for flow in all_accumulated_results
                    if flow['Timestamp'].startswith(today_date_str)
                ]
                
                if not filtered_results:
                    print("No flow data found for today's date.")
                    # If no data for today, skip saving this iteration and continue loop
                    # The main loop's sleep will handle the delay
                    continue # Skip the rest of the current loop iteration

                # Sort all results by premium before saving (optional, but keeps consistency)
                filtered_results.sort(key=lambda x: x['Premium'], reverse=True)
                # Take top LIMIT results
                final_results = filtered_results[:LIMIT]
                
                # Save all accumulated results to the consistent JSON file
                try:
                    with open(OUTPUT_JSON_FILE, 'w') as f:
                        json.dump(final_results, f, indent=4)
                    print(f"\nCycle finished. All results saved to: {OUTPUT_JSON_FILE} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    print(f"Error saving results to {OUTPUT_JSON_FILE}: {e}")
            else:
                print("No results found to save.")

            # Wait for 5 minutes before next update
            print(f"\nWaiting 5 minutes until next update...")
            time.sleep(300)
    except Exception as main_loop_exception:
        print(f"An error occurred in the main loop: {main_loop_exception}")
        # Consider adding a longer sleep here if persistent errors occur
        time.sleep(60)