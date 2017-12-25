import pandas
import tushare as ts

import atexit
import os

class PriceData(object):
    """description of class"""
    
    INTERVALS = ["day", "5min", "15min", "30min", "60min"]
    IFENG_INTERVAL_MAP = {"day" : "D", "5min" : "5", "15min" : "15", "30min" : "30", "60min" : "60"}

    def __init__(self, code, csv_base_name, today_date, time_of_day):
        self.code = code
        self.csv_base_name = csv_base_name
        if (self.csv_base_name is not None):
            self.initiate_from_csv(csv_base_name)
            if (not self.is_up_to_date(today_date)):
                self.merge_hist_data()
            elif (not self.is_today_data_up_to_time(time_of_day)):
                self.merge_today_data()
        else:
            self.initiate_from_ifeng_hist_data()

    def initiate(self):
        self.update_timestamp()
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

    def update_timestamp(self):
        """
        Set the time of last update from loaded data. 

        self.date_last_update = 
        self.time_last_update = 
        """

    def is_up_to_date(self, today_date):
        # TODO: do real things
        return True

    def is_today_data_up_to_time(self, time_of_day):
        # TODO: do real things
        return True

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
