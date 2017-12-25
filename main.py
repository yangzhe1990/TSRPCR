from CSI300 import CSI300
from SimpleMovingAverage import SimpleMovingAverage

csi300 = CSI300()
csi300.initiate_from_ifeng_data()
for sma_name in SimpleMovingAverage.DEFAULT_PARAMS.keys():
    date, ma = csi300.price_data.sma.sma[sma_name][0][1][0]
    print("Moving average %s at %s:\t%s" % (sma_name, date, ma))
