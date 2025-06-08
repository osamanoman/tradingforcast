import sys
import os
import json
from pathlib import Path
from datetime import datetime
import time # Import the time module

# Add the project root to sys.path to allow importing modules
current_dir = os.getcwd()
sys.path.append(current_dir)

# Import functions from your modules
from modules.ticker_dwn import dwn_data as download_ticker_data
from modules.calc import get_options_data_json # Assuming this function is the entry point in calc.py for processing json data

def ensure_directories():
    """Create necessary directories if they don't exist."""
    data_dir = Path(f"{os.getcwd()}/data")
    json_dir = data_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)

def process_and_save_gamma_data(ticker: str):
    """Processes data for a single ticker and saves the gamma analysis.

    Args:
        ticker: The ticker symbol.
    """
    print(f"Processing gamma data for {ticker}...")
    # Assuming get_options_data_json in modules.calc can take ticker and expiry and return the processed data
    # We might need to adjust the function signature or create a new wrapper in modules.calc if needed.
    # For now, let's assume it can process the data from the saved json.
    
    # Need to determine the correct way to call functions in calc.py to get the final gamma data structure
    # Based on the previous script, it involved reading the raw data and calling calc_exposures.
    # Let's try to replicate that logic using functions from modules.calc
    
    try:
        # The get_options_data_json function in calc.py seems to read the raw json and perform calculations
        # It requires a ticker, expiry ('all', 'monthly', '0dte', 'opex'), and timezone.
        # Let's process for 'all' expiry for now.
        # Timezone might need to be dynamic or configurable.
        # Assuming 'America/New_York' as a default timezone.
        
        # Need to handle potential errors if the raw data file doesn't exist or is 'Unavailable'
        raw_data_path = Path(f"{os.getcwd()}/data/json/{ticker.lower()}_quotedata.json")
        if not raw_data_path.exists():
            print(f"Raw data file not found for {ticker}: {raw_data_path}")
            return
            
        with open(raw_data_path, 'r') as f:
            raw_data = json.load(f)
            
        if raw_data == "Unavailable":
            print(f"Raw data unavailable for {ticker}")
            return
            
        # Now call the processing logic from modules.calc
        # The get_options_data_json function returns a tuple, we need the structured data for the frontend
        # Looking back at the previous script, the structure needed for the frontend was created separately.
        # Let's refine this based on the structure expected by app/api/gamma/data/route.ts
        
        # The get_options_data_json function in calc.py returns a tuple:
        # (option_data, today_ddt, today_ddt_string, monthly_options_dates, spot_price, from_strike, to_strike, levels.ravel(), totaldelta, totalgamma, totalvanna, totalcharm, zerodelta, zerogamma, call_ivs, put_ivs)
        
        # We need to structure this into the format expected by the frontend API:
        # {
        #     'ticker': ticker.upper(),
        #     'spotPrice': spot_price,
        #     'expiryData': {
        #         'expiry_date_1': { 'strikeData': [...], 'totalExposure': ..., 'zeroGamma': ... },
        #         'expiry_date_2': { 'strikeData': [...], 'totalExposure': ..., 'zeroGamma': ... },
        #         ...
        #     },
        #     'lastUpdated': datetime.now().isoformat()
        # }
        
        # The calc_exposures function in calc.py calculates the exposure data.
        # The get_options_data_json function in calc.py calls calc_exposures after formatting the data.
        
        # Let's try calling get_options_data_json with 'all' expiry and a default timezone.
        timezone = 'America/New_York'
        processing_results = get_options_data_json(ticker, 'all', timezone)
        
        if processing_results is None:
            print(f"Failed to process data for {ticker}")
            return
            
        # Extract the necessary parts from the processing results tuple
        (option_data_df, today_ddt, today_ddt_string, monthly_options_dates, spot_price, from_strike, to_strike, levels, totaldelta, totalgamma, totalvanna, totalcharm, zerodelta, zerogamma, call_ivs, put_ivs) = processing_results
        
        # Now structure this into the frontend format
        # Need to group the option_data_df by expiry and calculate total exposure and zero gamma for each expiry.
        
        expiry_data = {}
        # Iterate through unique expiry dates in the dataframe
        for expiry in option_data_df['expiration_date'].unique():
            expiry_str = expiry.strftime('%Y-%m-%d') # Format expiry date as string
            
            # Filter dataframe for the current expiry
            expiry_df = option_data_df[option_data_df['expiration_date'] == expiry].copy()
            
            # Calculate total exposure for this expiry
            total_exposure = expiry_df['total_gamma'].sum() # Assuming total_gamma is the relevant metric for totalExposure
            
            # Structure strike data for this expiry
            strike_data = []
            # Need to determine how strikeData should be structured based on the frontend needs.
            # The previous script created strike_data based on individual options.
            # Let's assume strikeData should be a list of strikes and their aggregated exposures for this expiry.
            
            # Group by strike price and sum exposures for this expiry
            strike_exposure_agg = expiry_df.groupby('strike_price')[['call_gex', 'put_gex', 'total_gamma']].sum().reset_index()
            
            for index, row in strike_exposure_agg.iterrows():
                 strike_data.append({
                    'strike': row['strike_price'],
                    'callExposure': row['call_gex'] / 10**9, # Scale down similar to total gamma
                    'putExposure': row['put_gex'] / 10**9, # Scale down
                    'totalExposure': row['total_gamma'] # Already scaled down in calc_exposures
                 })
            
            # Find zero gamma point for this expiry if needed. The calc_exposures function already calculated a zero gamma for the 'all' expiry.
            # If the frontend needs zero gamma per expiry, we might need to adjust calc.py or calculate it here.
            # For now, let's just include the overall zero gamma calculated by calc_exposures if this is for the 'all' expiry.
            # If processing by individual expiry ('0dte', 'opex', 'monthly'), calc_exposures would return expiry-specific zero gamma.
            # Let's stick to processing 'all' expiry in this script and provide the overall zero gamma.
            
            # The zero_gamma value from the tuple is for the 'all' calculation. We need expiry-specific zero gamma.
            # This indicates we might need to adjust the processing logic or how calc.py is used.
            # Let's reconsider how the previous process_gamma_data.py worked.
            # It calculated exposures for 'all', 'ex_next', 'ex_fri' expiries and had logic for zero gamma.
            # It also had functions get_options_data_json/csv which seem to filter by expiry before calling calc_exposures.
            # This suggests we should call get_options_data_json for each expiry type needed by the frontend ('all', 'monthly', '0dte', 'opex').
            
            pass # This logic will be replaced below
            
    except Exception as e:
        print(f"Error processing data for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return

def main():
    """Main function to fetch, process, and save gamma data for all tickers."""
    ensure_directories()
    
    # Define tickers and expiry types
    tickers = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "SPX"]
    expiry_types = ['all', 'monthly', '0dte', 'opex'] # Expiry types needed by the frontend
    timezone = 'America/New_York'
    
    # Ensure raw data is downloaded (optional, can be run separately)
    # download_ticker_data(select=tickers, is_json=True) # Download data for all tickers in JSON format
    
    print("Starting continuous gamma data processing...")

    while True: # Infinite loop to run continuously
        print(f"Processing cycle started at {datetime.now()}")
        
        # Ensure raw data is downloaded inside the loop for continuous updates
        print("Downloading latest raw data...")
        download_ticker_data(select=tickers, is_json=True) # Download data for all tickers in JSON format
        print("Raw data download finished.")

        for ticker in tickers:
            gamma_data_for_frontend = {
                'ticker': ticker.upper(),
                'spotPrice': None, # Will get this from the first processing run
                'expiryData': {},
                'lastUpdated': datetime.now().isoformat()
            }
            
            spot_price = None
            
            for expiry_type in expiry_types:
                print(f"Processing {ticker} for {expiry_type} expiry...")
                try:
                    processing_results = get_options_data_json(ticker, expiry_type, timezone)
                    
                    if processing_results is None:
                        print(f"Skipping {ticker} for {expiry_type} expiry due to processing failure or unavailable data.")
                        continue
                    
                    (option_data_df, today_ddt, today_ddt_string, monthly_options_dates, current_spot_price, from_strike, to_strike, levels, totaldelta, totalgamma, totalvanna, totalcharm, zerodelta, zerogamma, call_ivs, put_ivs) = processing_results
                    
                    # Get spot price from the first successful processing run
                    if spot_price is None:
                        spot_price = current_spot_price
                        gamma_data_for_frontend['spotPrice'] = spot_price
                        
                    # Structure strike data for this expiry type
                    strike_data = []
                    # We need strike-level exposure data for this specific expiry_type.
                    # The option_data_df filtered by get_options_data_json contains only options for this expiry_type.
                    # Group by strike and sum exposures.
                    
                    # Ensure expected columns exist before grouping
                    # Removed explicit column check as output shows columns are present
                    # required_cols = ['strike_price', 'call_gex', 'put_gex', 'total_gamma', 'call_dex', 'put_dex', 'total_delta', 'call_vex', 'put_vex', 'total_vanna', 'call_cex', 'put_cex', 'total_charm']
                    
                    # Strip whitespace from required columns for robust checking
                    # required_cols_stripped = [col.strip() for col in required_cols]
                    # Strip whitespace from DataFrame columns as well
                    # df_columns_stripped = [col.strip() for col in option_data_df.columns]

                    # Perform the check using stripped column names
                    # if not all(col in df_columns_stripped for col in required_cols_stripped):
                    #     print(f"Skipping {ticker} for {expiry_type} expiry: Missing required columns in processed data.")
                    #     print(f"Available columns: {option_data_df.columns.tolist()}") # Print as list for clarity
                    #     print(f"Required columns: {required_cols}")
                    #     continue

                    # Group by strike price and sum exposures for this expiry type
                    strike_exposure_agg = option_data_df.groupby('strike_price')[['call_gex', 'put_gex', 'total_gamma', 'call_dex', 'put_dex', 'total_delta', 'call_vex', 'put_vex', 'total_vanna', 'call_cex', 'put_cex', 'total_charm']].sum().reset_index()

                    for index, row in strike_exposure_agg.iterrows():
                        # Include exposures for all Greeks
                        strike_data.append({
                            'strike': row['strike_price'],
                            'gamma': {
                                'callExposure': row['call_gex'] / 10**9, # Scale down
                                'putExposure': row['put_gex'] / 10**9, # Scale down
                                'totalExposure': row['total_gamma'] # Already scaled down
                            },
                            'delta': {
                                'callExposure': row['call_dex'] / 10**9, # Scale down
                                'putExposure': row['put_dex'] / 10**9, # Scale down
                                'totalExposure': row['total_delta'] / 10**9 # Scale down
                            },
                            'vanna': {
                                'callExposure': row['call_vex'] / 10**9, # Scale down
                                'putExposure': row['put_vex'] / 10**9, # Scale down
                                'totalExposure': row['total_vanna'] / 10**9 # Scale down
                            },
                            'charm': {
                                'callExposure': row['call_cex'] / 10**9, # Scale down
                                'putExposure': row['put_cex'] / 10**9, # Scale down
                                'totalExposure': row['total_charm'] / 10**9 # Scale down
                            }
                        })
                    
                    # Include total exposure and zero gamma for this expiry type
                    # The totalgamma and zerogamma from the tuple are for the data subset based on expiry_type filter.
                    # total_gamma is the array of total gamma values across strike levels.
                    # total_delta is the array of total delta values across strike levels.
                    # zerogamma is the zero gamma point for this expiry_type based on total gamma curve.
                    # zerodelta is the zero delta point for this expiry_type based on total delta curve.
                    
                    # The frontend expects 'totalExposure' as a single number for the expiry group, which should be the total gamma exposure.
                    # This is the sum of total_gamma for all strikes in this expiry.
                    total_gamma_exposure_for_expiry = option_data_df['total_gamma'].sum()
                    
                    gamma_data_for_frontend['expiryData'][expiry_type] = {
                        'strikeData': strike_data,
                        'totalExposure': float(total_gamma_exposure_for_expiry), # Ensure it's a float for JSON
                        'zeroGamma': float(zerogamma) if zerogamma is not None else None # Ensure it's a float or None
                    }
                    
                except Exception as e:
                    print(f"Error processing {ticker} for {expiry_type} expiry: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                    
            # Save the combined gamma data for the ticker
            if spot_price is not None and gamma_data_for_frontend['expiryData']: # Only save if we got data
                output_path = Path(f"{os.getcwd()}/data/json/{ticker.lower()}_gamma.json")
                with open(output_path, 'w') as f:
                    json.dump(gamma_data_for_frontend, f, indent=2) # Save the entire structured dictionary
                print(f"Saved gamma analysis for {ticker} to {output_path}")
            elif spot_price is None:
                 print(f"Skipping save for {ticker}: Could not get spot price or process any expiry data.")
            else:
                 print(f"Skipping save for {ticker}: No valid expiry data processed.")

        print(f"Processing cycle finished at {datetime.now()}")
        time.sleep(300) # Wait for 5 seconds before the next cycle

if __name__ == "__main__":
    main() 