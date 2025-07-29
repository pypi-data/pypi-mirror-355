from thsdk import THS, Interval, Adjust
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo

bj_tz = ZoneInfo('Asia/Shanghai')

with THS() as ths:
    response = ths.market_block("USHA")
    print("沪市场:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(0.1)

    response = ths.market_block("USZA")
    print("深市场:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(0.1)

    response = ths.market_block("USTM")
    print("京市场:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(0.1)

    response = ths.market_block("UNQS")
    print("美股纳斯达克:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(0.1)

    response = ths.market_block("UFXB")
    print("汇率市场:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(0.1)

    response = ths.market_block("USHI")
    print("沪指数:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(0.1)

    response = ths.market_block("UIFB")
    print("期权:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(0.1)

    response = ths.market_block("UEUA")
    print("英国:")
    print(pd.DataFrame(response.payload.result))
    time.sleep(0.1)




