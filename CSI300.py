import tushare as ts

from FakePriceDataLoader import FakePriceDataLoaderChina
from PriceData import PriceData
from SimpleMovingAverage import SimpleMovingAverage

import PriceDataLoader

from datetime import datetime

class CSI300(object):
    CSI300_CODE_IFENG = "sh000300"

    def __init__(self):
        start_datetime = datetime(2017, 12, 27, 14, 49, 59)
        csv_base_name = "csi300"
        # Fake data source to debug realtime data updating and SMA calculation.
        PriceDataLoader.price_data_loader_china = FakePriceDataLoaderChina(start_datetime, csv_base_name)

        self.price_data = PriceData(CSI300.CSI300_CODE_IFENG, csv_base_name)
        self.price_data.set_simple_moving_average(SimpleMovingAverage(SimpleMovingAverage.DEFAULT_PARAMS))

        self.price_data.update_realtime()
