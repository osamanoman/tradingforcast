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
import concurrent.futures

# --- Configuration ---
API_KEY = "M563eKqwZduqpb0G5PUlaqpAKpoGnmVi"
UNDERLYING_TICKERS = ["ARKK" , "XLE" , "EFA" , "EFA", "SMH" , "GDX" , "XLF" , "EEM" , "XLF", "EWZ" , "FXI" , "LQD" , "SQQQ" , "SLV", "TSLL" , "KWEB" , "HYG" , "SOXL" , "TQQQ", "IBIT" , "GLD" , "TLT" , "IWM" , "QQQ", "SPY"]  # List of indices to process
MIN_PREMIUM_THRESHOLD = 0  # $0 minimum premium
MIN_VOLUME = 100  # Minimum volume threshold
MIN_OPEN_INTEREST = 100  # Minimum open interest threshold
MAX_DAYS_TO_EXPIRATION = 200  # Maximum days until expiration
LIMIT = 50

# Create output directory if it doesn't exist
OUTPUT_DIR = os.path.join("gflows-main", "data", "json")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

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
                print(f"\nProcessing contract {contract_count}: {option_ticker}")
                
                # Parse expiration date and contract details
                expiry_date, strike_price, option_type = parse_options_ticker(option_ticker)
                if expiry_date:
                    exp_date = datetime.strptime(expiry_date, "%Y-%m-%d")
                    days_to_exp = (exp_date - current_date).days
                    
                    # Filter by expiration date
                    if days_to_exp > MAX_DAYS_TO_EXPIRATION:
                        print(f"Skipping: Expiration too far ({days_to_exp} days)")
                        continue
                else:
                    print(f"Could not parse expiration date from {option_ticker}")
                    continue

                # Get last trade
                trades = client.list_trades(option_ticker, limit=1)
                if not trades:
                    print(f"No trades found for {option_ticker}")
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

                # Filter by minimum volume
                if volume < MIN_VOLUME:
                    print(f"Skipping: Volume ({volume}) below minimum threshold ({MIN_VOLUME})")
                    continue

                # Filter by minimum open interest
                if open_interest < MIN_OPEN_INTEREST:
                    print(f"Skipping: Open Interest ({open_interest}) below minimum threshold ({MIN_OPEN_INTEREST})")
                    continue

                # Determine side (Bid/Ask)
                side = "-"
                if last_trade:
                    bid = getattr(last_trade, 'bid', 0)
                    ask = getattr(last_trade, 'ask', 0)
                    if price <= bid:
                        side = "Bid"
                    elif price >= ask:
                        side = "Ask"

                # Format conditions
                condition_str = ','.join(map(str, getattr(last_trade, 'conditions', []))) if last_trade else "-"

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
                print(f"Added data for {contract_name}")

            except Exception as e:
                print(f"Error processing contract {option_ticker}: {str(e)}")
                continue

        print(f"\nProcessed {contract_count} contracts for {ticker}")
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
    print(f"Récupération du flux d'options pour {', '.join(UNDERLYING_TICKERS)}")
    print(f"Filtres: Premium > ${MIN_PREMIUM_THRESHOLD:,}, Volume > {MIN_VOLUME:,}, Open Interest > {MIN_OPEN_INTEREST:,}, Max Days to Expiration: {MAX_DAYS_TO_EXPIRATION}")

    # Define a fixed filename for the latest data
    LATEST_FILENAME = os.path.join(OUTPUT_DIR, "option_flows_latest.json")

    while True:
        # --- Running data fetch and analysis ---
        print(f"\n--- Running data fetch and analysis at {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')} ---")
        all_results = []

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
                        all_results.extend(flow_results)
                except Exception as exc:
                    print(f'{ticker} generated an exception: {exc}')

        if all_results:
            # Get today's date in YYYY-MM-DD format for filtering
            today_date_str = datetime.now().strftime("%Y-%m-%d")

            # Filter results for the same date as today
            filtered_results = [
                flow for flow in all_results
                if flow['Timestamp'].startswith(today_date_str)
            ]
            
            if not filtered_results:
                print("No flow data found for today's date.")
                # If no data for today, we might want to skip saving this iteration
                # Or handle it differently based on desired behavior
                time.sleep(300) # Still wait if no data for today to avoid tight loop
                continue # Skip the rest of the current loop iteration

            # Sort all results by premium
            filtered_results.sort(key=lambda x: x['Premium'], reverse=True)
            # Take top LIMIT results
            final_results = filtered_results[:LIMIT]

            # Print results to console
            print_flow_table(final_results)

            # Save to JSON
            try:
                # Convert to JSON and save to the latest file
                with open(LATEST_FILENAME, 'w') as f:
                    json.dump(final_results, f, indent=4)
                print(f"\nResults saved to: {LATEST_FILENAME}")
            except Exception as e:
                print(f"Error saving results to {LATEST_FILENAME}: {e}")
        else:
            print("No results found to process or save.")

        # Wait for 5 minutes before the next run
        print("\nWaiting 5 minutes before next fetch...")
        time.sleep(300)