import tushare as ts

import atexit

from PriceData import PriceData

class PriceDataManager(object):
    """description of class"""

    def __init__(self, code, csv_path, today_date, time_of_day):
        self.code = code
        self.csv_path = csv_path
        if (self.csv_path is not None):
            self.initiate_from_csv(csv_path)
            if (not self.is_up_to_date()):
                self.merge_hist_data()
            else:
                if 
        else:
            self.initiate_from_ifeng_hist_data()

    def initiate(self):
        atexit.register(PriceDataManager.save_csv, self)

    def initiate_from_csv(self, csv_path):
        # TODO: load
        self.initiate()

    def initiate_from_ifeng_hist_data(self):
        self.price_data = self.get_ifeng_hist_data()
        self.initiate()
    
    def get_ifeng_hist_data(self):
        # Download from ifeng
        price_data = {}
        price_data["day"] = ts.stock.trading.get_hist_data(code = CSI300.CSI300_CODE_IFENG)
        for minute_interval in ["5", "15", "30", "60"]:
            price_data[minute_interval + "min"] = ts.stock.trading.get_hist_data(code = CSI300.CSI300_CODE_IFENG, ktype = minute_interval)
        return price_data


