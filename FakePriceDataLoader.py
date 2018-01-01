from PriceData import PriceData
from TradingDateTime import TradingDateTime, trading_date_time

import PriceDataLoader

import pandas

import datetime
import os

# A class to fake price data.
class FakePriceDataLoaderChina(PriceDataLoader.PriceDataLoaderChina):
    def __init__(self, start_datetime, csv_base_name):
        # fake_now_str must be multiple of 5 minute
        self.fake_now_str = \
            trading_date_time.previousIntervalClose("5min",
                trading_date_time.closeTimeOfCurrentMinuteIntervalChina(5, start_datetime, check_opening = False).strftime(TradingDateTime.DATETIME_STRFTIME))

        self.csv_base_name = csv_base_name

        self.csv_path_to_interval_name = {}
        self.ktype_to_interval_name = {}
        for (interval, ktype) in PriceData.INTERVAL_TO_REQUEST_MAP.items():
            self.ktype_to_interval_name[ktype] = interval

        self.price_data = {}
        self.load_data_from_csv(csv_base_name, start_datetime)

    def load_data_from_csv(self, csv_base_name, start_datetime):
        for interval in PriceData.INTERVALS:
            csv_path = "%s_%s.csv" % (self.csv_base_name, interval)
            if os.path.exists(csv_path):
                df = pandas.read_csv(csv_path, index_col = 0)
            else:
                raise Exception()
            self.price_data[interval] = df
            self.csv_path_to_interval_name[csv_path] = interval

    def cut_price_data_by_datetime(self, price_data, datetime_str):
        return price_data.loc[price_data.index <= datetime_str]

    def get_fake_price_data_for_interval(self, interval):
        if interval == PriceData.DAY:
            day_str, time_str = self.fake_now_str.split()
            if (time_str == "15:00:00"):
                datetime_str = day_str
            else:
                datetime_str = trading_date_time.previousTradingDayChina(day_str)
        else:
            datetime_str = self.fake_now_str
        return self.cut_price_data_by_datetime(self.price_data[interval], datetime_str)

    """ Inherited methods. """
    def get_hist_data(self, code = None, start = None, end = None, ktype= 'D', retry_count = 3, pause = 0.001):
        raise Exception()

    def get_k_data(self, code = None, start = '', end = '', ktype = 'D', autype = 'qfq', index = False, retry_count = 3, pause = 0.001):
        data = self.get_fake_price_data_for_interval(self.ktype_to_interval_name[ktype])
        data = data.reset_index()
        if ktype != 'D':
            # Simulate the tencent's data format for minute intervals.
            size = len(data.index)
            for i in range(size):
                data.at[i, "date"] = data.at[i, "date"][:-3]
        return data

    def get_realtime_quotes(self, symbols = None):
        # Increase fake_now_str by 5 minutes and return the price by fake_now_str
        now_str = trading_date_time.nextIntervalClose("5min", self.fake_now_str)

        # Return value format: DataFrame with only one record, containing price in "price", date in "date", time in "time".
        # If datetime goes beyond our data, always return the last one, and stop the fake_now_str increasing.
        if now_str in self.price_data["5min"].index:
            self.fake_now_str = now_str
        else:
            now_str = self.fake_now_str
        date, time = now_str.split()
        price = self.price_data["5min"].at[date + " " + time, "close"]
        return pandas.DataFrame(data = {"price": [price], "date": [date], "time": [time]})
    
    def read_csv(self, filepath, **kwargs):
        interval = self.csv_path_to_interval_name[filepath]
        return self.get_fake_price_data_for_interval(interval)

    def save_csv(self, df, csv_path):
        return

    def now(self):
        return datetime.datetime.strptime(self.fake_now_str, TradingDateTime.DATETIME_STRFTIME)
