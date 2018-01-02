from TradingDateTime import TradingDateTime, trading_date_time
from PriceDataLoader import price_data_loader_china

import pandas

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
        # Simple moving average.
        self.sma = None
        # Realtime price data.
        self.realtime_price_data = {}

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
        return price_data_loader_china.get().get_hist_data(code = self.code, ktype = PriceData.INTERVAL_TO_REQUEST_MAP[interval])

    """ WARNING: tencent data sometimes contain gaps, make sure to discard data before gap when calculating indicators such as moving average. """
    def get_tencent_hist_data_by_interval(self, interval):
        data = price_data_loader_china.get().get_k_data(code = self.code, ktype = PriceData.INTERVAL_TO_REQUEST_MAP[interval])

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
        data = data.set_index("date").sort_index()
        return data

    def merge_tencent_hist_data(self, interval):
        data = self.get_hist_data_by_interval(interval)
        merged = pandas.merge(self.price_data[interval].reset_index(), data.reset_index(), how = "outer").set_index("date")
        # Dedup because data record from long ago in two responses sometimes are different.
        # This is one issue of Tencent data source. One record must be wrong and we take the newest value.
        deduped = merged[~merged.index.duplicated(keep = "last")]
        # Tencent data may can contain gap within data records so we must sort after merging.
        self.price_data[interval] = deduped.sort_index()

    def update_hist_data(self, now):
        last_closed_day = trading_date_time.lastClosedDayChina(now)
        # Check for daily data.
        if last_closed_day > self.__get_last_datetime(PriceData.DAY):
            self.merge_hist_data(PriceData.DAY)

        # Check for minutes data.
        for interval in PriceData.INTERVALS:
            if (interval.endswith("min")):
                interval_min = int(interval[:-3])
                last_interval_close = trading_date_time.lastClosedMinuteIntervalTimeChina(interval_min, now)
                if (last_interval_close.strftime(TradingDateTime.DATETIME_STRFTIME) > self.__get_last_datetime(interval)):
                    self.merge_hist_data(interval)

    def get_hist_data_by_interval(self, interval):
        data = self.get_tencent_hist_data_by_interval(interval)
        print("last price record:\n%s" % self.get_last_price_record(data))
        return data

    def merge_hist_data(self, interval):
        print("Update data for %s" % interval)
        # Get the last datetime string of the data before update
        last_datetime_str = self.get_last_price_record(self.price_data[interval]).name
        self.merge_tencent_hist_data(interval)
        if self.sma is not None:
            self.sma.append_price_records(interval, last_datetime_str, self.price_data[interval])

    def save_csv(self):
        for interval in PriceData.INTERVALS:
            self.__save_data_frame_to_csv(self.price_data[interval], "%s_%s.csv" % (self.csv_base_name, interval))
    
    def update_realtime(self, fakeNow = None):
        if not trading_date_time.isRealtimeDataAvailableChina(fakeNow):
            print("Not requesting realtime data because trade has closed.")
            return
        data = price_data_loader_china.get().get_realtime_quotes(self.code).iloc[0]
        print(data)
        price = float(data["price"])
        time_str = "%s %s" % (data["date"], data["time"])
        for interval in PriceData.INTERVALS:
            self.__update_realtime_at_interval(interval, price, time_str)

    def set_simple_moving_average(self, sma):
        self.sma = sma
        sma.load_price_data(self.price_data)

    """ Print a summary of last price data including history data and realtime data at each interval. """
    def print_realtime_price_summary(self):
        for interval in PriceData.INTERVALS:
            print("Last price record of interval %s: %s" % (interval, self.get_last_price_record(self.price_data[interval])))
            # Realtime price data may not be available when trading is already closed.
            if interval in self.realtime_price_data:
                print("Realtime data at %s: %s" % (interval, self.realtime_price_data[interval]))

    """ Print a summary of realtime sma information. """
    def print_realtime_sma_summary(self):
        if self.sma is not None:
            self.sma.print_realtime_sma_summary(self.price_data, self.realtime_price_data)

    def __update_realtime_at_interval(self, interval, price, time_str):
        # Compute the close time of the current interval.
        time = datetime.datetime.strptime(time_str, TradingDateTime.DATETIME_STRFTIME)
        if interval == PriceData.DAY:
            this_close = time_str.split(' ')[0]
        else:
            this_close = trading_date_time.closeTimeOfCurrentMinuteIntervalChina(
                int(interval[:-3]), time, check_opening = False).strftime(TradingDateTime.DATETIME_STRFTIME)

        # Obtain interval data. Create if it doesn't exist.
        interval_data = self.realtime_price_data.get(interval, None)
        if interval_data is None:
            interval_data = self.realtime_price_data[interval] = {"this_close": this_close}

        # Interval data exists but has shifted. In this case we would like to replace the existing one.
        if interval_data.get("this_close") != this_close:
            new_interval_data = {
                "prev_close_price": interval_data["last_price"],
                "prev_close": interval_data["this_close"],
                "this_close": this_close,
                }
            interval_data = self.realtime_price_data[interval] = new_interval_data

        # Update interval data.
        interval_data["last_price"] = price
        interval_data["last_time"] = time_str

    def get_last_price_record(self, price_data):
        return price_data.iloc[len(price_data.index) - 1]

    def __save_data_frame_to_csv(self, df, csv_path):
        price_data_loader_china.get().save_csv(df, csv_path)

    def __load_data_frame_from_csv(self, csv_path):
        if os.path.exists(csv_path):
            return price_data_loader_china.get().read_csv(csv_path, index_col = 0)
        else:
            print("File not found: %s. Will do fresh download instead." % csv_path)
            return None

    def __get_last_datetime(self, interval):
        return self.get_last_price_record(self.price_data[interval]).name
