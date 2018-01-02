import tushare as ts

from FakePriceDataLoader import FakePriceDataLoaderChina
from PriceData import PriceData
from SimpleMovingAverage import SimpleMovingAverage

import PriceDataLoader

import time
import threading

from datetime import datetime

class CSI300(object):
    CSI300_CODE_IFENG = "sh000300"

    def __init__(self, realtime_polling_interval = 20):
        start_datetime = datetime(2017, 12, 27, 14, 49, 59)
        csv_base_name = "csi300"
        # Fake data source to debug realtime data updating and SMA calculation.
        #PriceDataLoader.price_data_loader_china = FakePriceDataLoaderChina(start_datetime, csv_base_name)

        self.price_data = PriceData(CSI300.CSI300_CODE_IFENG, csv_base_name)
        self.price_data.set_simple_moving_average(SimpleMovingAverage(SimpleMovingAverage.DEFAULT_PARAMS))

        self.realtime_polling_interval = realtime_polling_interval
        self.start_realtime_polling()
        self.start_histdata_polling()

        while True:
            try:
                self.realtime_polling_thread.join(timeout = 5)
                self.histdata_polling_thread.join(timeout = 5)
                if not self.realtime_polling_thread.is_alive() or not self.histdata_polling_thread.is_alive():
                    print("At least one of the polling thread finished.")
                    self.stop_realtime_polling()
                    self.stop_histdata_polling()
                    break
            except (KeyboardInterrupt, SystemExit):
                print("Ctrl-C or SystemExit.")
                self.stop_realtime_polling()
                self.stop_histdata_polling()

    def start_realtime_polling(self):
        self.realtime_polling = True
        self.realtime_polling_thread = threading.Thread(target = self.realtime_price_polling)
        self.realtime_polling_thread.start()

    def stop_realtime_polling(self):
        self.realtime_polling = False
        # TODO: In order to quit ASAP we need to signal the thread to force sleep to finish.
        # However we don't care too much about it now.

    def start_histdata_polling(self):
        self.histdata_polling = True
        self.histdata_polling_thread = threading.Thread(target = self.history_price_data_polling)
        self.histdata_polling_thread.start()

    def stop_histdata_polling(self):
        self.histdata_polling = False
        # TODO: same as above.

    def realtime_price_polling(self):
        while self.realtime_polling:
            self.price_data.update_realtime()
            self.price_data.print_realtime_price_summary()
            self.price_data.print_realtime_sma_summary()
            time.sleep(self.realtime_polling_interval)

    def history_price_data_polling(self):
        while self.histdata_polling:
            time.sleep(1)
            nowChina = PriceDataLoader.price_data_loader_china.now()
            self.price_data.update_hist_data(nowChina)
# bug: update data for day