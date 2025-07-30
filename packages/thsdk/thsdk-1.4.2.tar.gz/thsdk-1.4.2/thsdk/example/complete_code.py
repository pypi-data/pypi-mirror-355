from thsdk import THS, Interval, Adjust
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo

with THS() as ths:
    response = ths.complete_code("300033")
    print("补齐单个:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    codes = ["300033", "600519", "TSLA", "APPL", "159316", "1A0001"]
    response = ths.complete_code(codes)
    print("补齐多个:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    if len(codes) < len(response.payload.result):
        print("可能获取到多市场数据，检查代码")
    if len(codes) > len(response.payload.result):
        print("补齐错误于原数据数量不匹配")
    time.sleep(1)
