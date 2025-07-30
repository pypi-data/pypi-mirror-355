from thsdk import THS
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo

with THS() as ths:
    response = ths.tick_super_level1("USZA300033")
    print("超级盘口:")
    if not response.is_success():
        print(f"错误信息: {response.err_info}")

    df = pd.DataFrame(response.get_result())
    df["时间"] = pd.to_datetime(df["时间"], unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Shanghai")
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    print(df)
    time.sleep(1)
