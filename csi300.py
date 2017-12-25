import tushare as ts

from PriceData import PriceData
from SimpleMovingAverage import SimpleMovingAverage

class CSI300(object):
    CSI300_CODE_IFENG = "sh000300"

    def __init__(self):
        self.price_data = PriceData(CSI300.CSI300_CODE_IFENG, "csi300", None, None)
        self.price_data.setSimpleMovingAverage(SimpleMovingAverage(SimpleMovingAverage.DEFAULT_PARAMS))
