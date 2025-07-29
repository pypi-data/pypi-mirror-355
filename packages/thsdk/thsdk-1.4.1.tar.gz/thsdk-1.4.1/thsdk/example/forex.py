from thsdk import THS, Interval, Adjust
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo

bj_tz = ZoneInfo('Asia/Shanghai')

with THS() as ths:
    response = ths.forex_list()
    print("基本汇率:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

