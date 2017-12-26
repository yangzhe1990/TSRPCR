from TradingDateTime import TradingDateTime, trading_date_time

import pandas
import tushare as ts

import atexit
import os

class PriceData(object):
    """For A shares traded in Shanghai / Shenzhen."""
    
    DAY = "day"
    INTERVALS = [DAY, "5min", "15min", "30min", "60min"]
    IFENG_INTERVAL_MAP = {DAY : "D", "5min" : "5", "15min" : "15", "30min" : "30", "60min" : "60"}

    def __init__(self, code, csv_base_name, now = None):
        self.code = code
        self.csv_base_name = csv_base_name
        if (self.csv_base_name is not None):
            self.initiate_from_csv(csv_base_name)
            self.update_hist_data(now)
        else:
            self.initiate_from_ifeng_hist_data()

    def initiate(self):
        atexit.register(PriceData.save_csv, self)

    """ Initiate from saved csv file but fall back to downloading in case of missing files """
    def initiate_from_csv(self, csv_base_name):
        self.price_data = {}
        for interval in PriceData.INTERVALS:
            df = self.__load_data_frame_from_csv("%s_%s.csv" % (self.csv_base_name, interval))
            if df is None:
                df = self.get_ifeng_hist_data_by_interval(interval)
            self.price_data[interval] = df

        self.initiate()

    def initiate_from_ifeng_hist_data(self):
        self.price_data = self.get_ifeng_hist_data()
        self.initiate()
        
    """ Download from ifeng. """
    def get_ifeng_hist_data_by_interval(self, interval):
        return ts.stock.trading.get_hist_data(code = self.code, ktype = PriceData.IFENG_INTERVAL_MAP[interval])
    
    def get_ifeng_hist_data(self):
        price_data = {}
        for interval in PriceData.INTERVALS:
            price_data[interval] = self.get_ifeng_hist_data_by_interval(interval)
        return price_data

    """ TODO: this method doesn't work because ifeng_hist_data may not give data of the current trading day! """
    def update_hist_data(self, now):
        last_closed_day = trading_date_time.lastClosedDayChina(now)
        # Check for daily data.
        if last_closed_day > self.price_data[PriceData.DAY].iloc[0].name:
            self.merge_ifeng_hist_data(PriceData.DAY)

        # Check for minutes data.
        for interval in PriceData.INTERVALS:
            if (interval.endswith("min")):
                interval_min = int(interval[:-3])
                last_interval_close = trading_date_time.lastClosedMinuteIntervalTimeChina(interval_min, now)
                if (last_interval_close.strftime(TradingDateTime.DATETIME_STRFTIME) > self.price_data[interval].iloc[0].name):
                    self.merge_ifeng_hist_data(interval)

    def merge_ifeng_hist_data(self, interval):
        print("Update data for %s" % interval)
        data = self.get_ifeng_hist_data_by_interval(interval)
        self.price_data[interval] = pandas.merge(data.reset_index(), self.price_data[interval].reset_index(), how = "outer").set_index("date")

    def save_csv(self):
        for interval in PriceData.INTERVALS:
            self.__save_data_frame_to_csv(self.price_data[interval], "%s_%s.csv" % (self.csv_base_name, interval))
    
    def setSimpleMovingAverage(self, sma):
        self.sma = sma
        sma.loadPriceData(self.price_data)

    def appendPriceData(self, price_tick):
        self.sma.appendPriceData(price_tick)
        
    def __save_data_frame_to_csv(self, df, csv_path):
        df.to_csv(csv_path)

    def __load_data_frame_from_csv(self, csv_path):
        if os.path.exists(csv_path):
            return pandas.read_csv(csv_path, index_col = 0)
        else:
            print("File not found: %s. Will do fresh download instead." % csv_path)
            return None
