import tushare as ts

from PriceData import PriceData
from SimpleMovingAverage import SimpleMovingAverage

class CSI300(object):
    CSI300_CODE_IFENG = "sh000300"

    def initiate_from_ifeng_data(self):
        # Download from ifeng
        price_data = {}
        price_data["day"] = ts.stock.trading.get_hist_data(code = CSI300.CSI300_CODE_IFENG)
        for minute_interval in ["5", "15", "30", "60"]:
            price_data[minute_interval + "min"] = ts.stock.trading.get_hist_data(code = CSI300.CSI300_CODE_IFENG, ktype = minute_interval)
        
        # Convert data format
        # For now just print what we've got.
        for interval in ["day", "5min", "15min", "30min", "60min"]:
            print("Data for %s" % interval)
            print(price_data[interval])

        # Create price data
        self.price_data = PriceData(price_data)
        self.price_data.setSimpleMovingAverage(SimpleMovingAverage(SimpleMovingAverage.DEFAULT_PARAMS))
