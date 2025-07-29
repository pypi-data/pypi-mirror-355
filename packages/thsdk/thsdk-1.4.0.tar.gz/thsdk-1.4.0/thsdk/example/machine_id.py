from thsdk import THS, Interval, Adjust
import pandas as pd
import time

with THS() as ths:
    print(ths.machine_id())
    time.sleep(1)
