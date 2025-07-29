from thsdk import THS, Interval, Adjust
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo

with THS() as ths:
    response = ths.depth("USZA300033")
    print("单只五档:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")

    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)

    response = ths.depth(["USZD123234", "USZD123184", "USZD123093", "USZD123093", ])
    print("多支五档:")
    if response.errInfo != "":
        print(f"错误信息: {response.errInfo}")
    print(pd.DataFrame(response.payload.result))
    time.sleep(1)
