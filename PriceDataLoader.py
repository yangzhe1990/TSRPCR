import pandas
import tushare as ts

import datetime
import pytz

# A delegate class of methods to get price data.
# Program should only call an instance of this class for price data.
class PriceDataLoaderChina(object):
    # For users who do from ... import price_data_loader_china, to make sure that they get
    # the current price_data_loader_china instance.
    def get(self):
        return price_data_loader_china
    def checkInstanceUnchanged(self):
        equal = self == price_data_loader_china
        if not equal:
            raise Exception()
    def get_hist_data(self, code = None, start = None, end = None, ktype= 'D', retry_count = 3, pause = 0.001):
        self.checkInstanceUnchanged()
        return ts.stock.trading.get_hist_data(code, start, end, ktype, retry_count, pause)
    def get_k_data(self, code = None, start = '', end = '', ktype = 'D', autype = 'qfq', index = False, retry_count = 3, pause = 0.001):
        self.checkInstanceUnchanged()
        return ts.stock.trading.get_k_data(code, start, end, ktype, autype, index, retry_count, pause)
    def get_realtime_quotes(self, symbols = None):
        self.checkInstanceUnchanged()
        return ts.stock.trading.get_realtime_quotes(symbols)
    def read_csv(self, filepath, **kwargs):
        self.checkInstanceUnchanged()
        return pandas.read_csv(filepath, **kwargs)
    def save_csv(self, df, csv_path):
        self.checkInstanceUnchanged()
        df.to_csv(csv_path)
    def now(self):
        self.checkInstanceUnchanged()
        return datetime.datetime.now(pytz.timezone('Asia/Shanghai'))

# The instance which delegates loading of price data.
# Initialized as fake price data loader to debug. 
price_data_loader_china = PriceDataLoaderChina()
