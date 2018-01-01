import tushare as ts

from PriceDataLoader import price_data_loader_china

import bisect
import datetime

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

    """ Whether realtime data is available at given time on a trading day. If so, today is not fully closed. """
    def isRealtimeDataAvailableChina(self, nowChina = None):
        if nowChina is None:
            nowChina = self.nowChina()
        if not self.isTradingDayChina(nowChina.strftime(TradingDateTime.DAY_STRFTIME)):
            return False
        time = (nowChina.hour, nowChina.minute, nowChina.second)
        return (TradingDateTime.CHINA_OPENING_AUCTION_CLOSE <= time and time <= TradingDateTime.CHINA_MORNING_CLOSE) or \
            (TradingDateTime.CHINA_AFTERNOON_OPEN <= time and time <= TradingDateTime.CHINA_AFTERNOON_CLOSE)

    """ Get the last closed day before given datetime. Return date format is YYYY-MM-DD. [0, 1) -> 0 """
    def lastClosedDayChina(self, nowChina = None):
        if nowChina is None:
            nowChina = self.nowChina()
        day_str = nowChina.strftime(TradingDateTime.DAY_STRFTIME)
        # Return today if today is trading day and it's already closed now.
        if self.isTradingDayChina(day_str) and ((nowChina.hour, nowChina.minute, nowChina.second) >= TradingDateTime.CHINA_AFTERNOON_CLOSE):
            return day_str
        # Otherwise return the previous trading day.
        else:
            return self.previousTradingDayChina(day_str)

    """ Get the first trading day where close time is not before the given datetime. Return date format is YYYY-MM-DD. (0, 1] -> 1 """
    def dayToCloseChina(self, nowChina = None):
        if nowChina is None:
            nowChina = self.nowChina()
        day_str = nowChina.strftime(TradingDateTime.DAY_STRFTIME)
        # Return today if today is trading day and it's not yet closed.
        if self.isTradingDayChina(day_str) and ((nowChina.hour, nowChina.minute, nowChina.second) <= TradingDateTime.CHINA_AFTERNOON_CLOSE):
            return day_str
        # Otherwise return the next trading day.
        else:
            return self.nextTradingDayChina(day_str)

    """ Date format is YYYY-MM-DD. [1] -> 0 """
    def previousTradingDayChina(self, day_str):
        index = bisect.bisect_left(self.getChinaTradingDates(), day_str)
        return "0000-01-01" if index == 0 else self.getChinaTradingDates()[index - 1]

    """ Date format is YYYY-MM-DD. [0] -> 1 """
    def nextTradingDayChina(self, day_str):
        index = bisect.bisect_right(self.getChinaTradingDates(), day_str)
        return "" if index == len(self.getChinaTradingDates()) else self.getChinaTradingDates()[index]

    """ Return a datetime object. [0, 1) -> 0 """
    def lastClosedMinuteIntervalTimeChina(self, minute_interval, nowChina = None):
        if (nowChina is None):
            nowChina = self.nowChina()
        day_str = nowChina.strftime(TradingDateTime.DAY_STRFTIME)

        # Return previous closed day if today is not trading day or the time from today's open is less than minute_interval.
        if not self.isTradingDayChina(day_str) or \
            (nowChina.hour * 60 + nowChina.minute < 
                TradingDateTime.CHINA_MORNING_OPEN[0] * 60 + TradingDateTime.CHINA_MORNING_OPEN[1] + minute_interval):
            day_str = datetime.datetime.strptime(self.previousTradingDayChina(day_str), TradingDateTime.DAY_STRFTIME)
            return datetime.datetime.combine(day_str,
                datetime.time(TradingDateTime.CHINA_AFTERNOON_CLOSE[0], TradingDateTime.CHINA_AFTERNOON_CLOSE[1], TradingDateTime.CHINA_AFTERNOON_CLOSE[2], tzinfo = nowChina.tzinfo))
        # last closed minute interval time is in today.
        else:
            # Check if now is later than afternoon close.
            hm = (nowChina.hour, nowChina.minute, 0)
            if hm >= TradingDateTime.CHINA_AFTERNOON_CLOSE:
                (hour, minute, _) = TradingDateTime.CHINA_AFTERNOON_CLOSE
            # Check if now is past the first interval in afternoon trading.
            elif nowChina.hour * 60 + nowChina.minute >= TradingDateTime.CHINA_AFTERNOON_OPEN[0] * 60 + TradingDateTime.CHINA_AFTERNOON_OPEN[1] + minute_interval:
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

    """ Return a datetime object. (0, 1] -> 1 """
    def closeTimeOfCurrentMinuteIntervalChina(self, minute_interval, nowChina, check_opening = True):
        if check_opening and not self.isTradingDayChina(nowChina.strftime(TradingDateTime.DAY_STRFTIME)):
            return None
        hour, minute, second = (nowChina.hour, nowChina.minute, nowChina.second)
        # Check if now is in the morning
        is_morning = (hour, minute, second) < TradingDateTime.CHINA_AFTERNOON_OPEN
        if is_morning:
            second_of_opening = TradingDateTime.CHINA_MORNING_OPEN[0] * 3600 + TradingDateTime.CHINA_MORNING_OPEN[1] * 60 + TradingDateTime.CHINA_MORNING_OPEN[2]
        else:
            second_of_opening = TradingDateTime.CHINA_AFTERNOON_OPEN[0] * 3600 + TradingDateTime.CHINA_AFTERNOON_OPEN[1] * 60 + TradingDateTime.CHINA_AFTERNOON_OPEN[2]
        elapsed_second = hour * 3600 + minute * 60 + second - second_of_opening
        # If time is before opening, set the time to 1s after opening so that the math in the section below works.
        if elapsed_second <= 0:
            elapsed_second = 1

        # Round up because the last interval may not be full (e.g. 60min interval can not be full if total trading hour is 3h30min).
        close_minute = ((elapsed_second - 1) // (minute_interval * 60) + 1) * minute_interval + second_of_opening // 60
        close_hour = close_minute // 60
        close_minute = close_minute % 60
        if is_morning:
            if (close_hour, close_minute, 0) > TradingDateTime.CHINA_MORNING_CLOSE:
                close_hour, close_minute, _ = TradingDateTime.CHINA_MORNING_CLOSE
        else:
            if (close_hour, close_minute, 0) > TradingDateTime.CHINA_AFTERNOON_CLOSE:
                close_hour, close_minute, _ = TradingDateTime.CHINA_AFTERNOON_CLOSE

        return datetime.datetime(nowChina.year, nowChina.month, nowChina.day, close_hour, close_minute, 0, tzinfo = nowChina.tzinfo)

    """ Given a minute interval and close time of an interval, return the close time of the previous interval. [1] -> 0 """
    def previousMinuteIntervalClose(self, minute_interval, close_time):
        day_str = close_time.strftime(TradingDateTime.DAY_STRFTIME)
        hour, minute = close_time.hour, close_time.minute
        # Check if now is in the morning.
        # It doesn't matter whether it's < or <= here because the first close_time in the afternoon can not be CHINA_AFTERNOON_OPEN.
        is_morning = (hour, minute, 0) < TradingDateTime.CHINA_AFTERNOON_OPEN
        if is_morning:
            minute_of_opening = TradingDateTime.CHINA_MORNING_OPEN[0] * 60 + TradingDateTime.CHINA_MORNING_OPEN[1]
        else:
            minute_of_opening = TradingDateTime.CHINA_AFTERNOON_OPEN[0] * 60 + TradingDateTime.CHINA_AFTERNOON_OPEN[1]
        elapsed_minute = hour * 60 + minute - minute_of_opening

        close_minute = (elapsed_minute - 1) // minute_interval * minute_interval + minute_of_opening
        close_hour = close_minute // 60
        close_minute = close_minute % 60

        if (close_hour, close_minute, 0) == TradingDateTime.CHINA_MORNING_OPEN:
            close_hour, close_minute, _ = TradingDateTime.CHINA_AFTERNOON_CLOSE
            day_str = self.previousTradingDayChina(day_str)
        elif (close_hour, close_minute, 0) == TradingDateTime.CHINA_AFTERNOON_OPEN:
            close_hour, close_minute, _ = TradingDateTime.CHINA_MORNING_CLOSE

        day = datetime.datetime.strptime(day_str, TradingDateTime.DAY_STRFTIME)
        return datetime.datetime.combine(day, datetime.time(close_hour, close_minute, 0, tzinfo = close_time.tzinfo))

    """ Given an interval and a datetime string, return the close datetime string of the previous interval. [1] -> 0 """
    def previousIntervalClose(self, interval, datetime_str):
        # Import here to break circular dependency.
        from PriceData import PriceData
        if interval == PriceData.DAY:
            return self.previousTradingDayChina(datetime_str)
        else:
            return self.previousMinuteIntervalClose(
                    int(interval[:-3]), datetime.datetime.strptime(datetime_str, TradingDateTime.DATETIME_STRFTIME)
                ).strftime(TradingDateTime.DATETIME_STRFTIME)

    """  Given a minute interval and close time of an interval, return the close time of the next interval. [0] -> 1 """
    def nextMinuteIntervalClose(self, minute_interval, close_time):
        day_str = close_time.strftime(TradingDateTime.DAY_STRFTIME)
        hms = (close_time.hour, close_time.minute, close_time.second)
        if hms == TradingDateTime.CHINA_AFTERNOON_CLOSE:
            day_str = self.nextTradingDayChina(day_str)
            hour, minute, _ = TradingDateTime.CHINA_MORNING_OPEN
        elif hms == TradingDateTime.CHINA_MORNING_CLOSE:
            hour, minute, _ = TradingDateTime.CHINA_AFTERNOON_OPEN
        else:
            hour, minute, _ = hms

        # In morning
        if (hour, minute, 0) < TradingDateTime.CHINA_AFTERNOON_OPEN:
            minute += minute_interval
            hour += minute // 60
            minute = minute % 60
            if (hour, minute, 0) > TradingDateTime.CHINA_MORNING_CLOSE:
                hour, minute, _ = TradingDateTime.CHINA_MORNING_CLOSE
        else:
            minute += minute_interval
            hour += minute // 60
            minute = minute % 60
            if (hour, minute, 0) > TradingDateTime.CHINA_AFTERNOON_CLOSE:
                hour, minute, _ = TradingDateTime.CHINA_AFTERNOON_CLOSE

        day = datetime.datetime.strptime(day_str, TradingDateTime.DAY_STRFTIME)
        return datetime.datetime.combine(day, datetime.time(hour, minute, 0, tzinfo = close_time.tzinfo))

    """ Given an interval and a datetime string, return the close datetime string of the next interval. [0] -> 1 """
    def nextIntervalClose(self, interval, datetime_str):
        # Import here to break circular dependency.
        from PriceData import PriceData
        if interval == PriceData.DAY:
            return self.nextTradingDayChina(datetime_str)
        else:
            return self.nextMinuteIntervalClose(
                    int(interval[:-3]), datetime.datetime.strptime(datetime_str, TradingDateTime.DATETIME_STRFTIME)
                ).strftime(TradingDateTime.DATETIME_STRFTIME)

    def nowChina(self):
        return price_data_loader_china.get().now()

    """ Date format is YYYY-MM-DD """
    def todayStringChina(self):
        return self.nowChina().strftime(TradingDateTime.DAY_STRFTIME)

trading_date_time = TradingDateTime()
