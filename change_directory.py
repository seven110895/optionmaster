# This file list all the directories that will be used in the options project, for both input and output files.
import os

class directory:
    def __init__(self):
        # Change directory if all data downloads and calculated are to be saved to a different directory.
        self.project_dir=os.getcwd()

    def data_download(self, type):
        if type=='option':
            type_folder='/Option Data/'
        elif type=='future':
            type_folder='/Futures Data/'
        elif type=='perpetual':
            type_folder='/Perpetual Data/'
        else:
            type_folder='/Other Data/'
        data_dir=self.project_dir+type_folder
        if not os.path.isdir(data_dir):
            os.mkdir(data_dir)
        return data_dir

    def trade_folder_dir(self):
        trade_folder_dir=self.project_dir+'/Trade/'
        if not os.path.isdir(trade_folder_dir):
            os.mkdir(trade_folder_dir)
        return  trade_folder_dir

    def trade_quantity_plot_dir(self, date):
        trade_plot_dir=self.trade_folder_dir()+'HourlyPlot_'+date+'.png'
        return trade_plot_dir

    def trade_dir(self, date):
        trade_dir=self.trade_folder_dir()+'deribitTrade'+date+'.csv'
        return trade_dir

    def trade_stats_file_dir(self, date, type):
        if type=='option':
            sub_folder='Option Trades/'
            filename='OptionTrades_'
        elif type=='future':
            sub_folder='Future Trades/'
            filename='FutureTrades_'
        elif type=='perpetual':
            sub_folder='Perpetual Trades/'
            filename='PerpetualTrades_'
        else:
            sub_folder='Other Trades/'
            filename='OtherTrades_'
        data_folder=self.trade_folder_dir()+'Data/'
        if not os.path.isdir(data_folder):
            os.mkdir(data_folder)
        sub_folder_dir=data_folder+sub_folder
        if not os.path.isdir(sub_folder_dir):
            os.mkdir(sub_folder_dir)
        trade_stats_dir=sub_folder_dir+'Deribit_'+filename+date+'.csv'
        return trade_stats_dir

    def straddle_result_dir(self, date):
        straddle_folder=self.project_dir+'/Straddle/'
        if not os.path.isdir(straddle_folder):
            os.mkdir(straddle_folder)
        straddle_dir=straddle_folder+'Straddle_'+date+'.csv'
        return straddle_dir

    def implied_vol_result_dir(self, date):
        implied_vol_folder=self.project_dir+'/Implied Vol/'
        if not os.path.isdir(implied_vol_folder):
            os.mkdir(implied_vol_folder)
        implied_vol_result_folder=implied_vol_folder+'Result File/'
        if not os.path.isdir(implied_vol_result_folder):
            os.mkdir(implied_vol_result_folder)
        implied_vol_dir=implied_vol_result_folder+'Implied_Vol_'+date+'.csv'
        return implied_vol_dir

    def implied_vol_plot_dir(self, time):
        implied_vol_folder = self.project_dir + '/Implied Vol/'
        if not os.path.isdir(implied_vol_folder):
            os.mkdir(implied_vol_folder)
        implied_vol_plot_folder=implied_vol_folder+'Plots/'
        if not os.path.isdir(implied_vol_plot_folder):
            os.mkdir(implied_vol_plot_folder)
        vol_plot_dir=implied_vol_plot_folder+time+'.csv'
        return vol_plot_dir

    def implied_vol_compare_dir(self,date):
        implied_vol_folder = self.project_dir + '/Implied Vol/'
        if not os.path.isdir(implied_vol_folder):
            os.mkdir(implied_vol_folder)
        implied_vol_compare_folder = implied_vol_folder + 'Compare/'
        if not os.path.isdir(implied_vol_compare_folder):
            os.mkdir(implied_vol_compare_folder)
        vol_compare_dir = implied_vol_compare_folder+'Implied_Vol_Compare_' + date + '.xlsx'
        return vol_compare_dir

    def implied_vol_plot_dir(self, date):
        implied_vol_folder = self.project_dir + '/Implied Vol/'
        if not os.path.isdir(implied_vol_folder):
            os.mkdir(implied_vol_folder)
        implied_vol_compare_folder = implied_vol_folder + 'Compare/'
        if not os.path.isdir(implied_vol_compare_folder):
            os.mkdir(implied_vol_compare_folder)
        implied_vol_plot_folder = implied_vol_compare_folder + 'plot/'
        if not os.path.isdir(implied_vol_plot_folder):
            os.mkdir(implied_vol_plot_folder)
        vol_plot_dir = implied_vol_plot_folder + 'Implied_Vol_Plot_' + date + '.pdf'
        return vol_plot_dir


    def realtime_orderbook_dir(self,date):
        realtime_orderbook_folder = self.project_dir + '/Realtime Orderbook/'
        if not os.path.isdir(realtime_orderbook_folder):
            os.mkdir(realtime_orderbook_folder)
        realtime_orderbook_dir = realtime_orderbook_folder+str(date) +'.csv'
        return realtime_orderbook_dir





