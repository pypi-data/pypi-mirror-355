from thsdk import THS, Interval, Adjust
import pandas as pd
import time

with THS() as ths:
    print(f"binding ID: {ths.binding_id()}")
    time.sleep(1)
