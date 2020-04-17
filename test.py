import os
import pandas as pd
import numpy as np
from Black_Scholes import BlackScholes
import re
import datetime
import matplotlib.pyplot as plt
from change_directory import directory
from matplotlib.backends.backend_pdf import PdfPages

def get_greeks(row, greek):
    b_s = BlackScholes(row['underlying_price'], 0, 0, row['mtr'])
    if greek == 'gamma':
        result =  b_s.BS_gamma(row['Strike'], row['m_mid_vol'])
    elif greek == 'theta':
        result = b_s.BS_theta(row['Strike'], row['m_mid_vol'], row['CallPut'])
    elif greek == 'vega':
        result = b_s.BS_vega(row['Strike'], row['m_mid_vol'])
    elif greek == 'delta':
        result = b_s.BS_delta(row['Strike'], row['m_mid_vol'], row['CallPut'])
    elif greek == 'vanna':
        result = b_s.BS_vanna(row['Strike'], row['m_mid_vol'])
    elif greek == 'volga':
        result = b_s.BS_volga(row['Strike'], row['m_mid_vol'])
    elif greek == 'gamma_deri':
        result = b_s.BS_gamma_deri(row['Strike'], row['m_mid_vol'])
    return result

def cal_ttm(row):
    tradetime = datetime.datetime.strptime(row['Date'], '%Y-%m-%d') + datetime.timedelta(hours= 16)
    mtr = datetime.datetime.strptime(row['Maturity'], '%Y-%m-%d') + datetime.timedelta(hours= 8)
    ttm = (mtr - tradetime).total_seconds() / (365 * 24 * 60 * 60)
    return ttm


All_df = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/All_implied_Vol_tradedistance10.csv")
All_df['mtr'] = All_df.apply(cal_ttm,axis = 1)
All_df['theta'] = All_df.apply(get_greeks, greek = 'theta', axis = 1)
All_df['vega'] = All_df.apply(get_greeks, greek = 'vega', axis = 1)
All_df.to_csv("D:/optionmaster/Straddle/Straddle_vol/All_implied_Vol_tradedistance10.csv")






