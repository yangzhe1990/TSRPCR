"""
price_data = {"day" : day_data, "5min" : ..., "60min" : ...}
day_data (etc.) : pandas.DataFrame(columns = ["date", "open", "high", "close", "low", "volume", "price_change", ...], ...)

Code should not assume any order of columns. Rows are sorted in most-recent-first order. 
"""

class PriceData(object):
    INTERVALS = ["day", "5min", "15min", "30min", "60min"]

    def __init__(self, price_data):
        self.price_data = price_data

    def setSimpleMovingAverage(self, sma):
        self.sma = sma
        sma.loadPriceData(self.price_data)

    def appendPriceData(self, price_tick):
        self.sma.appendPriceData(price_tick)
