import pandas as pd
import re
import os
import calendar
import datetime
import numpy as np

from DataClient import DataClient
from read_file import get_data
from change_directory import directory

start_date = datetime.date.today() - datetime.timedelta(days = 2)
end_date = datetime.date.today() - datetime.timedelta(days = 1)

output_dir=directory()
for d in np.arange(start_date, end_date):
    date=np.datetime64(d).astype(datetime.date)

    # Initiate the underlying values
    client = DataClient('3.17.63.79', 22, 'ec2-user', 'Waa9b25xyk')
    client.connect()
    arr = client.getfiles(str(date).replace("-",""), 'BTC')
    for f in arr:
        f_to_list = f.split('-')
        #  Options:
        if len(f_to_list) > 3:
            cp_date=re.split('_(\d+)', f_to_list[4])
            optionsDir = output_dir.data_download(type='option') + cp_date[1] + '_' + f_to_list[2] + '_' + f_to_list[3] + '_' + cp_date[0] +'.csv'
            if not os.path.exists(optionsDir):
                contractType = f_to_list[2].split('_')[0]
                if not contractType.startswith('PERP'):
                    options = get_data(f)
                    optionsDF = options.all_to_dataframe()
                    optionsDF.to_csv(path_or_buf=optionsDir)

        # Perpetuals
        if len(f_to_list) == 3:
            cp_date=re.split('_(\d+)', f_to_list[2])
            perpetualDir = output_dir.data_download(type='perpetual') + cp_date[1] + '_'+ cp_date[0] +'.csv'
            if not os.path.exists(perpetualDir):
                contractType = f_to_list[2].split('_')[0]
                if contractType.startswith('PERP'):
                    perpetual = get_data(f)
                    perpetualDF = perpetual.to_dataframe()
                    perpetualDF.to_csv(path_or_buf=perpetualDir)

        # Futures
        if len(f_to_list) == 3:
            cp_date=re.split('_(\d+)', f_to_list[2])
            futuresDir = output_dir.data_download(type='future') + cp_date[1] + '_' + cp_date[0] +'.csv'
            if not os.path.exists(futuresDir):
                contractType = f_to_list[2].split('_')[0]
                if not contractType.startswith('PERP'):
                    futures = get_data(f)
                    futuresDF = futures.to_dataframe()
                    futuresDF.to_csv(path_or_buf=futuresDir)
        print('Finished: ', date, f)