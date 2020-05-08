# OptionResearch

1. Daily trade volume:
    - Daily_Trade_Volumn.py will create an excel about the daily trade volume among different hours. 

2. Implied volatility compare:
    - implied_vol_compare.py will compare the implied vols we calculate according to the orderbook data with the snapshot data
    from Deribit website.

3. File directory:
    - change_directory.py will create folders to save data and results.

4. Straddle backtest:
    - conditional_straddle_backtest.py uses options with strike closest to the underlying price, and maturity of 30 days (constructed by one <30 days and one >30 days maturity).
    - The straddle backtest will run through all dates available. If data missing for some dates in the middle, the test will skip the dates, and simply rebalance the weight in the next available date.
    - This straddle will rebalance the short position everyday according to its portfolio delta
    - data_clean.py will help to clean the original data and calculate some params that we need in constructing the straddle.

5. Historical implied vol:
    - all_implied_vol_historical.py can be used to get the historical bid-ask price, implied vol, greeks of all options at 
    utc 16:00:00 from 2019-10-01. 