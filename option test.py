from WindPy import *
import pandas as pd

w.start()

# 获取期权合约信息OptionContractRawData
OptionContractRawData = w.wset("optioncontractbasicinfo", "exchange=sse;windcode=510050.SH;status=trading")
OptionContractData=OptionContractRawData.Data

pd.DataFrame(OptionContractData)