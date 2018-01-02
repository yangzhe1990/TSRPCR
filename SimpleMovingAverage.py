from PriceData import PriceData
from TradingDateTime import trading_date_time

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
        # Use a similar stucture of params for filling moving average data.
        # sma = {"name" : [((interval_name, count), sma_series), ...], ...}
        # sma_series = [(date, sma), ...] with date in increasing order.
        self.sma = {}

    def load_price_data(self, price_data):
        for ma in self.params.keys():
            self.sma[ma] = []
            for interval_def in self.params[ma]:
                interval, count = interval_def
                self.sma[ma].append((interval_def, self.calculate_moving_average(interval, count, price_data[interval])))

    """ When last_datetime_str is not None, update the existing sma_series. Otherwise compute sma_series soly from the provided price_data. """
    def calculate_moving_average(self, interval, count, price_data, sma_series = [], last_datetime_str = None):
        price_series = price_data.loc[:, "close"]
        size = price_series.size
        if count != int(count) or count < 1:
            print("Count %s is invalid." % count)
            return sma_series

        # Scan price_series in reverse order to find the beginning of the last continuous price records.
        # Due to issue in our data source, the price data may contain gaps. So we only compute sma for the
        # last continuous price records.
        # Stop as soon as the price record of last_datetime_str for which sma is already calculated.
        start = size - 1
        close_datetime = price_series.index[start]
        while start > 0:
            if price_series.index[start - 1] == trading_date_time.previousIntervalClose(interval, close_datetime):
                start -= 1
                close_datetime = price_series.index[start]
                if close_datetime == last_datetime_str:
                    break
            else:
                print("Price data in %s contains hole: %s, %s" % (interval, price_series.index[start - 1], trading_date_time.previousIntervalClose(interval, close_datetime)))
                break
        # If we can not extend existing sma data.
        if not close_datetime == last_datetime_str:
            index = start + count
            if index > size:
                return []
            sum = 0.0
            while start < index:
                sum += price_series.iat[start]
                start += 1
            # Create new sma_series because we can not extend the existing sma_series.
            sma_series = [(price_series.index[start], sum / count)]
        else:
            index = start + 1
            # However we do not have enough price records yet.
            if index < count:
                return []

        while index < size:
            sma_series.append((price_series.index[index], sma_series[-1][1] + (price_series.iat[index] - price_series.iat[index - count]) / count))
            index += 1
        return sma_series

    def append_price_records(self, interval, last_datetime_str, price_data):
        for ma in self.params.keys():
            for index in range(len(self.sma[ma])):
                interval_def, sma_series = self.sma[ma][index]
                if (interval_def[0] == interval):
                    count = interval_def[1]
                    self.sma[ma][index] = (interval_def, self.calculate_moving_average(interval, count, price_data, sma_series, last_datetime_str))

    """
    Compute the moving average of count for price records in interval, with given realtime_price_data, at time_to_predict.
    The realtime data gives price at current time, which could be approximately used as close price of current interval.
    In case if price record of the last closed interval is missing from price_data, the realtime data may contain an approximate
    close price for previous interval.

    With time_to_predict unset, this function calculate the sma at the current interval of current time. With time_to_predict is
    set to a time in future, sma is calculated assuming that the price remains at the realtime price unless specified in future_price.
    """
    def calculate_realtime_moving_average(self, interval, count, price_data, sma_series, realtime_price_data,
            time_to_predict = None, future_price = None):
        sum = 0.0
        if time_to_predict is None:
            # Use incremental calculation by default unless there is no enough data.
            index = len(price_data.index) - 1
            last_datetime_str = price_data.index[index]
            update_count = 0
            datetime_str = realtime_price_data["this_close"]
            while datetime_str != last_datetime_str:
                datetime_str = trading_date_time.previousIntervalClose(interval, datetime_str)
                update_count += 1
            sum = 0.0
            if update_count > 0:
                sum += realtime_price_data["last_price"]
            prev_close_price = realtime_price_data.get("prev_close_price", None)
            if update_count > 1 and prev_close_price is None or update_count > 2:
                print("Missing data between %s and %s in interval %s." % (last_datetime_str, realtime_price_data["this_close"], interval))
                raise Exception()
            if update_count > 1:
                sum += prev_close_price
                # If we want to estimate missing data.
                sum += (update_count - 2) * price_data.iloc[index]["close"]
            if len(sma_series) > 0:
                sum += sma_series[-1][1] * count
                for i in range(update_count):
                    sum -= price_data.iloc[index - count + i + 1]["close"]
            elif update_count + index + 1 >= count:
                for i in range(count - update_count):
                    sum += price_data.iloc[index - i]["close"]
            else:
                # No enough price records.
                return None
        else:
            print("Unsupported")
            raise Exception()
        return sum / count

    def print_realtime_sma_summary(self, price_data, realtime_price_data):
        for ma in self.params.keys():
            print("Realtime MA for %s days:" % ma)
            for index in range(len(self.sma[ma])):
                interval_def, sma_series = self.sma[ma][index]
                interval, count = interval_def
                # Realtime price data may not be available when trading is already closed.
                if interval not in realtime_price_data:
                    continue
                realtime_ma = self.calculate_realtime_moving_average(interval, count, price_data[interval].copy(), sma_series, realtime_price_data[interval])
                if realtime_ma is None:
                    realtime_ma_str = "None\t"
                else:
                    realtime_ma_str = "%.3f" % realtime_ma
                print("\t%s\tat interval %s,\t%s" % (realtime_ma_str, interval, count))
