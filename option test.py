from WindPy import *
import pandas as pd

w.start()

# 获取期权合约信息OptionContractRawData
OptionContractRawData = w.wset("optioncontractbasicinfo", "exchange=sse;windcode=510050.SH;status=trading")
OptionContractData = pd.DataFrame(OptionContractRawData.Data).T
OptionContractData.columns = OptionContractRawData.Fields
OptionContractName = OptionContractData.wind_code.map(lambda x: str(x) + ".SH")
# 生成期权合约代码
OptionContractNameCode = ",".join(OptionContractName)
# 提取分钟级历史数据
aa = w.wsi(OptionContractNameCode, "open,high,low,close,volume,amt,chg,pct_chg,oi,begintime,endtime",
           "2019-10-30 09:00:00", "2019-10-31 18:25:00", "PriceAdj=F")

