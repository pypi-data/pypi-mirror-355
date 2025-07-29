from thsdk import THS, Interval, Adjust
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo

with THS() as ths:
    response = ths.block_data(0xCE5E)
    print("板块数据:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    response = ths.block_data(0x15)
    print("沪市A股:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    response = ths.block_data(0x1B)
    print("深市A股:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    response = ths.block_data(0xCA8B)
    print("北交所:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    response = ths.block_data(0xCFE4)
    print("创业板:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    response = ths.block_data(0xCFE4)
    print("科创板:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    response = ths.block_data(0xCE5E)
    print("概念:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    response = ths.block_data(0xCE5F)
    print("行业:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)
