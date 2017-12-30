import tushare as ts

from PriceData import PriceData
from SimpleMovingAverage import SimpleMovingAverage

from datetime import datetime

class CSI300(object):
    CSI300_CODE_IFENG = "sh000300"

    def __init__(self):
        self.price_data = PriceData(CSI300.CSI300_CODE_IFENG, "csi300")
        self.price_data.set_simple_moving_average(SimpleMovingAverage(SimpleMovingAverage.DEFAULT_PARAMS))

        self.price_data.update_realtime(datetime(2017, 12, 27, 14, 59, 59))
