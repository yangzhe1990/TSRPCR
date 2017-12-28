from TradingDateTime import TradingDateTime, trading_date_time

import pandas
import tushare as ts

import atexit
import datetime
import os

class PriceData(object):
    """For A shares traded in Shanghai / Shenzhen."""
    
    DAY = "day"
    INTERVALS = [DAY, "5min", "15min", "30min", "60min"]
    INTERVAL_TO_REQUEST_MAP = {DAY : "D", "5min" : "5", "15min" : "15", "30min" : "30", "60min" : "60"}

    def __init__(self, code, csv_base_name, now = None):
        self.code = code
        self.csv_base_name = csv_base_name
        if (self.csv_base_name is not None):
            self.initiate_from_csv(csv_base_name)
            self.update_hist_data(now)
        else:
            self.initiate_hist_data_from_web()

    def initiate(self):
        atexit.register(PriceData.save_csv, self)

    """ Initiate from saved csv file but fall back to downloading in case of missing files """
    def initiate_from_csv(self, csv_base_name):
        self.price_data = {}
        for interval in PriceData.INTERVALS:
            df = self.__load_data_frame_from_csv("%s_%s.csv" % (self.csv_base_name, interval))
            if df is None:
                df = self.get_hist_data_by_interval(interval)
            self.price_data[interval] = df

        self.initiate()

    def initiate_hist_data_from_web(self):
        self.price_data = self.download_hist_data()
        self.initiate()

    def download_hist_data(self):
        price_data = {}
        for interval in PriceData.INTERVALS:
            price_data[interval] = self.get_hist_data_by_interval(interval)
        return price_data

    """ DEPRECATED: Download from ifeng. ifeng_hist_data may not give data of the current trading day! """
    def get_ifeng_hist_data_by_interval(self, interval):
        return ts.stock.trading.get_hist_data(code = self.code, ktype = PriceData.INTERVAL_TO_REQUEST_MAP[interval])

    """ TODO: WARNING: tencent data sometimes contain gaps, try to discard data before gap when calculating indicators such as moving average. """
    def get_tencent_hist_data_by_interval(self, interval):
        data = ts.stock.trading.get_k_data(code = self.code, ktype = PriceData.INTERVAL_TO_REQUEST_MAP[interval])

        if interval.endswith("min"):
            # Fix date format for minute intervals.
            size = len(data.index)
            for i in range(size):
                data.at[i, "date"] = "%s:00" % data.at[i, "date"]
            # Remove irregular data. Tecent data gives one more minute record for current minute interval when trading!
            i = size - 1
            last_datetime = datetime.datetime.strptime(data.at[i, "date"], TradingDateTime.DATETIME_STRFTIME)
            close_datetime = trading_date_time.closeTimeOfCurrentMinuteIntervalChina(int(interval[:-3]), last_datetime)
            if last_datetime != close_datetime:
                print(last_datetime, close_datetime)
                data.drop(i, inplace = True)
        data = data.set_index("date").sort_index(ascending=False)
        return data

    def merge_tencent_hist_data(self, interval):
        data = self.get_hist_data_by_interval(interval)
        merged = pandas.merge(data.reset_index(), self.price_data[interval].reset_index(), how = "outer").set_index("date")
        # Dedup because data record from long ago in two responses sometimes are different.
        # This is one issue of Tencent data source. One record must be wrong and we take the newest value.
        deduped = merged[~merged.index.duplicated(keep = "first")]
        # Tencent data can contain gap within data records so we must sort after merging.
        self.price_data[interval] = deduped.sort_index(ascending=False)

    def update_hist_data(self, now):
        last_closed_day = trading_date_time.lastClosedDayChina(now)
        # Check for daily data.
        if last_closed_day > self.price_data[PriceData.DAY].iloc[0].name:
            self.merge_hist_data(PriceData.DAY)

        # Check for minutes data.
        for interval in PriceData.INTERVALS:
            if (interval.endswith("min")):
                interval_min = int(interval[:-3])
                last_interval_close = trading_date_time.lastClosedMinuteIntervalTimeChina(interval_min, now)
                if (last_interval_close.strftime(TradingDateTime.DATETIME_STRFTIME) > self.price_data[interval].iloc[0].name):
                    self.merge_hist_data(interval)

    def get_hist_data_by_interval(self, interval):
        data = self.get_tencent_hist_data_by_interval(interval)
        print(data.iloc[0])
        return data

    def merge_hist_data(self, interval):
        print("Update data for %s" % interval)
        self.merge_tencent_hist_data(interval)

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
