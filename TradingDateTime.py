import tushare as ts

import bisect
import datetime
import pytz

class TradingDateTime(object):
    """Provide local date time information of China stock exchange."""
    CHINA_OPENING_AUCTION_CLOSE = (9, 25, 0)
    CHINA_MORNING_OPEN = (9, 30, 0)
    CHINA_MORNING_CLOSE = (11, 30, 0)
    CHINA_AFTERNOON_OPEN = (13, 0, 0)
    CHINA_AFTERNOON_CLOSE = (15, 0, 0)

    DAY_STRFTIME = "%Y-%m-%d"
    DATETIME_STRFTIME = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        self.__ChinaTradingDates = None

    def getChinaTradingDates(self):
        # Check if China trading dates need update.
        if (self.__ChinaTradingDates is None) or (self.__ChinaTradingDates[-1] < self.todayStringChina()):
            calendar = ts.trade_cal()
            self.__ChinaTradingDates = calendar[calendar.isOpen == 1]['calendarDate'].values
        return self.__ChinaTradingDates

    def isTradingDayChina(self, day):
        index = bisect.bisect_left(self.getChinaTradingDates(), day)
        return day == self.getChinaTradingDates()[index]

    """ Whether realtime data is available at given time on a trading day. If so, today is not fully closed """
    def isRealtimeDataAvailableChina(self, nowChina = None):
        if nowChina is None:
            nowChina = self.nowChina()
        if not self.isTradingDayChina(nowChina.strftime(TradingDateTime.DAY_STRFTIME)):
            return False
        time = (nowChina.hour, nowChina.minute, nowChina.second)
        return (TradingDateTime.CHINA_OPENING_AUCTION_CLOSE <= time and time <= TradingDateTime.CHINA_MORNING_CLOSE) or \
            (TradingDateTime.CHINA_AFTERNOON_OPEN <= time and time <= TradingDateTime.CHINA_AFTERNOON_CLOSE)

    """ Date format is YYYY-MM-DD """
    def lastClosedDayChina(self, nowChina = None):
        if nowChina is None:
            nowChina = self.nowChina()
        today = nowChina.strftime(TradingDateTime.DAY_STRFTIME)
        # Return today if today is trading day and it's already closed now.
        if self.isTradingDayChina(today) and ((nowChina.hour, nowChina.minute, nowChina.second) >= TradingDateTime.CHINA_AFTERNOON_CLOSE):
            return today
        # Otherwise return the previous trading day.
        else:
            return self.previousTradingDayChina(today)

    """ Return a datetime object. """
    def lastClosedMinuteIntervalTimeChina(self, minute_interval, nowChina = None):
        if (nowChina is None):
            nowChina = self.nowChina()
        today = nowChina.strftime(TradingDateTime.DAY_STRFTIME)
        # Return previous closed day if today is not trading day or the time from today's open is less than minute_interval.
        if not self.isTradingDayChina(today) or \
            (nowChina.hour * 60 + nowChina.minute < 
                TradingDateTime.CHINA_MORNING_OPEN[0] * 60 + TradingDateTime.CHINA_MORNING_OPEN[1] + minute_interval):
            time = datetime.datetime.strptime(self.previousTradingDayChina(today), TradingDateTime.DAY_STRFTIME)
            return datetime.datetime.combine(time, 
                datetime.time(TradingDateTime.CHINA_AFTERNOON_CLOSE[0], TradingDateTime.CHINA_AFTERNOON_CLOSE[1], TradingDateTime.CHINA_AFTERNOON_CLOSE[2], tzinfo = nowChina.tzinfo))
        # last closed minute interval time is in today.
        else:
            # Check if now is later than afternoon close.
            hm = (nowChina.hour, nowChina.minute, 0)
            if hm >= TradingDateTime.CHINA_AFTERNOON_CLOSE:
                (hour, minute, _) = TradingDateTime.CHINA_AFTERNOON_CLOSE
            # Check if now is in afternoon trading.
            elif hm >= TradingDateTime.CHINA_AFTERNOON_OPEN:
                elapsed_minute = (nowChina.hour - TradingDateTime.CHINA_AFTERNOON_OPEN[0]) * 60 + nowChina.minute - TradingDateTime.CHINA_AFTERNOON_OPEN[1]
                elapsed_minute = elapsed_minute % minute_interval
                minute = nowChina.hour * 60 + nowChina.minute - elapsed_minute
                hour = minute // 60
                minute = minute % 60
            # Check if now is after morning close
            elif hm >= TradingDateTime.CHINA_MORNING_CLOSE:
                (hour, minute, _) = TradingDateTime.CHINA_MORNING_CLOSE
            # Now is in morning trading.
            else:
                elapsed_minute = (nowChina.hour - TradingDateTime.CHINA_MORNING_OPEN[0]) * 60 + nowChina.minute - TradingDateTime.CHINA_MORNING_OPEN[1]
                elapsed_minute = elapsed_minute % minute_interval
                minute = nowChina.hour * 60 + nowChina.minute - elapsed_minute
                hour = minute // 60
                minute = minute % 60

            return datetime.datetime(nowChina.year, nowChina.month, nowChina.day, hour, minute, 0, tzinfo = nowChina.tzinfo)

    def closeTimeOfCurrentMinuteIntervalChina(self, minute_interval, nowChina, check_opening = True):
        if check_opening and not self.isTradingDayChina(nowChina.strftime(TradingDateTime.DAY_STRFTIME)):
            return None
        hour, minute, second = (nowChina.hour, nowChina.minute, nowChina.second)
        # Check if now is in the morning
        is_morning = (hour, minute, second) <= TradingDateTime.CHINA_AFTERNOON_OPEN
        if is_morning:
            second_since_opening = TradingDateTime.CHINA_MORNING_OPEN[0] * 3600 + TradingDateTime.CHINA_MORNING_OPEN[1] * 60 + TradingDateTime.CHINA_MORNING_OPEN[2]
        else:
            second_since_opening = TradingDateTime.CHINA_AFTERNOON_OPEN[0] * 3600 + TradingDateTime.CHINA_AFTERNOON_OPEN[1] * 60 + TradingDateTime.CHINA_AFTERNOON_OPEN[2]
        elapsed_second = hour * 3600 + minute * 60 + second - second_since_opening

        close_minute = ((elapsed_second - 1) // (minute_interval * 60) + 1) * minute_interval + second_since_opening // 60
        close_hour = close_minute // 60
        close_minute = close_minute % 60
        if is_morning:
            if (close_hour, close_minute, 0) > TradingDateTime.CHINA_MORNING_CLOSE:
                close_hour, close_minute, _ = TradingDateTime.CHINA_MORNING_CLOSE
        else:
            if (close_hour, close_minute, 0) > TradingDateTime.CHINA_AFTERNOON_CLOSE:
                close_hour, close_minute, _ = TradingDateTime.CHINA_AFTERNOON_CLOSE

        return datetime.datetime(nowChina.year, nowChina.month, nowChina.day, close_hour, close_minute, 0, tzinfo = nowChina.tzinfo)

    """ Date format is YYYY-MM-DD """
    def previousTradingDayChina(self, day):
        index = bisect.bisect_left(self.getChinaTradingDates(), day)
        return "0000-01-01" if index == 0 else self.getChinaTradingDates()[index - 1]

    def nowChina(self):
        return datetime.datetime.now(pytz.timezone('Asia/Shanghai'))

    """ Date format is YYYY-MM-DD """
    def todayStringChina(self):
        return self.nowChina().strftime(TradingDateTime.DAY_STRFTIME)

trading_date_time = TradingDateTime()
