from PriceData import PriceData

class SimpleMovingAverage(object):
    DEFAULT_PARAMS = {
        "240" : [ # Annual 年线
            ("day", 240),
            ("60min", 960),
            ("30min", 1920),
            ("15min", 3840)
            ],
        "120" : [ # Semi-annual 半年线
            ("day", 120),
            ("60min", 480),
            ("30min", 960),
            ("15min", 1920),
            ],
        "60" : [ # Quarter 季线
            ("day", 60),
            ("60min", 240),
            ("30min", 480),
            ("15min", 960),
            ("5min", 2880),
            ],
        "30" : [ # Semi-Quarter 30日线，半季
            ("day", 30),
            ("60min", 120),
            ("30min", 240),
            ("15min", 480),
            ("5min", 1440),
            ],
        "20" : [ # Month 20日线，一个月
            ("day", 20),
            ("60min", 80),
            ("30min", 160),
            ("15min", 320),
            ("5min", 960),
            ],
        "10" : [ # Half-Month 10日线，半个月、两周
            # Most important resistence-line for mid-term trend, around which the price is usually hesistate, therefore set double line.
            # 中期趋势最重要的压力线/支撑线。股价在此附近经常反复，而回抽确认时可能稍高或稍低，因此设置双线。
            ("day", 10),
            ("60min", 38),
            ("60min", 48),
            ("30min", 77),
            ("30min", 99),
            ("15min", 150),
            ("15min", 170),
            ("5min", 320),
            ],
        "5" : [ # Week 5日线，一周
            ("day", 5),
            ("60min", 20),
            ("30min", 40),
            ("15min", 80),
            ("5min", 240),
            ],
        }

    def __init__(self, params):
        self.params = params

    def loadPriceData(self, price_data):
        self.price_data = price_data
        
        # Use a similar stucture of params for filling moving average data.
        # sma = {"name" : [((interval_name, count), sma_series), ...], ...}
        # sma_series = [(date, sma), ...]  as deque or stack
        self.sma = {}
        for ma in self.params.keys():
            self.sma[ma] = []
            for interval in self.params[ma]:
                self.sma[ma].append((interval, self.calculatePriceMovingAverage(interval[0], interval[1])))

    def calculatePriceMovingAverage(self, interval, count):
        # TODO: change data type of sma_series for efficient insertion at top
        sma_series = []
        price_data = self.price_data[interval]
        price_series = price_data.loc[:, "close"]

        last = 0
        sum = 0.0
        size = price_series.size

        if (count > size):
            return sma_series

        while (last < count):
            sum += price_series.iat[last]
            last += 1
        for priceTick in price_series.iteritems():
            sma_series.append((priceTick[0], sum / count))
            sum -= priceTick[1]
            sum += price_series.iat[last]
            last += 1
            if (last == size):
                break
        return sma_series

    def appendPriceData(self, price_tick):
        pass