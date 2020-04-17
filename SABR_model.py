import numpy as np
from scipy.optimize import minimize
import pandas as pd
import datetime
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

def lognormal_vol(k, f, t, alpha, beta, rho, volvol):
    #Hegan's paper log normal implied volatility, equation 2.17a
    if k <= 0 or f <= 0:
        return 0
    eps = 1e-07
    logfk = np.log(f / k)
    fkbeta = (f*k)**(1 - beta)
    a = (1 - beta) ** 2 * alpha ** 2 / (24 * fkbeta)
    b = 0.25 * rho * beta * volvol * alpha / fkbeta ** 0.5
    c = (2 - 3 * rho ** 2) * volvol ** 2 / 24
    d = fkbeta ** 0.5
    v = (1 - beta) ** 2 * logfk ** 2 / 24
    w = (1 - beta) ** 4 * logfk ** 4 / 1920
    z = volvol * fkbeta ** 0.5 * logfk / alpha
    if abs(z) > eps:
        vz = alpha * z * (1 + (a + b + c) * t) / (d * (1 + v + w) * _x(rho, z))
        return vz
        # if |z| <= eps
    else:
        v0 = alpha * (1 + (a + b + c) * t) / (d * (1 + v + w))
        return v0

def _x(rho, z):
    a = (1 - 2 * rho * z + z ** 2) ** .5 + z - rho
    b = 1 - rho
    return np.log(a / b)

def alpha(v_atm_ln, f, t, beta, rho, volvol):
    # use ATM lognormal volatility to calibrate the alpha parameter, use equation
    f_ = f ** (beta - 1)
    p = [
        t * f_ ** 3 * (1 - beta) ** 2 / 24,
        t * f_ ** 2 * rho * beta * volvol / 4,
        (1 + t * volvol ** 2 * (2 - 3 * rho ** 2) / 24) * f_,
        -v_atm_ln
    ]
    roots = np.roots(p)
    roots_real = np.extract(np.isreal(roots), np.real(roots))
    alpha_first_guess = v_atm_ln * f ** (1 - beta)
    i_min = np.argmin(np.abs(roots_real - alpha_first_guess))
    return roots_real[i_min]

def fit(f, t, beta, k, v_sln):
    # calibrate SABR parameters alpha, rho and volvol by the market obeserved k and implied log normal volatility
    def vol_square_error(x):
        vols = [lognormal_vol(k_,f,t,x[0],beta,x[1],x[2]) * 100 for k_ in k]
        return sum((vols - v_sln) **2)
    x0 = np.array([0.01, 0.00, 0.10])
    bounds = [(0.0001, None), (-0.9999, 0.9999), (0.0001, None)]
    res = minimize(vol_square_error, x0, method='L-BFGS-B', bounds=bounds)
    alpha, rho, volvol = res.x
    return [alpha, rho, volvol]

vol_historical = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/ALL_MTR_STRIKE.csv")

one_day_vol  = vol_historical.loc[vol_historical['Date'] == str(datetime.date(2019, 10, 1))]
mtr_options = one_day_vol.groupby('Maturity')
strike_list = np.arange(min(one_day_vol['Strike']), max(one_day_vol['Strike'])+100, 50)
vol_surface_df = pd.DataFrame(columns=strike_list)

pdf = PdfPages("D:/optionmaster/SABR_Vol/Vol_Curve_fit.pdf")
for mtr, one_day_mtr_vol in mtr_options:
    #one_day_mtr_vol  = one_day_vol[one_day_vol['Maturity'] == str(datetime.date(2019,10,4))]
    one_day_mtr_vol  = one_day_mtr_vol[one_day_mtr_vol['m_mid_vol'] != -1]
    one_day_mtr_vol_C = one_day_mtr_vol[one_day_mtr_vol['CallPut'] == 'C']
    t = (datetime.datetime.combine(np.datetime64(mtr).astype(datetime.date), datetime.time(8, 0, 0))
                         - datetime.datetime.combine(datetime.date(2019, 10, 1), datetime.time(16, 0, 0))).total_seconds() / (365 * 24 * 60 * 60)
    f = np.mean(one_day_mtr_vol_C['underlying_price'])
    beta = 1
    k = np.array(one_day_mtr_vol_C['Strike'])
    v_sln = np.array(one_day_mtr_vol_C['m_mid_vol'])
    param = fit(f, t, beta, k, v_sln)
    strike_list = np.arange(min(k), max(k) + 100, 50)
    vol_fit = [lognormal_vol(k_, f, t, param[0], beta, param[1], param[2]) * 100 for k_ in strike_list]
    vol_surface_df.loc[t, strike_list] = vol_fit
    plt.figure(figsize=(6, 6))
    fig = plt.figure(1)
    ax1 = plt.subplot(111)
    ax1.plot(strike_list, vol_fit)
    ax1.scatter(k, v_sln)
    ax1.set_xlabel('Strike')
    ax1.set_title(str(datetime.date(2019, 10, 1)) + ' SABR Vol Curve, Maturity :' + str(mtr))
    pdf.savefig()
    plt.close()
pdf.close()


