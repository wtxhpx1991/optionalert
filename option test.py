from WindPy import *
import pandas as pd
import datetime as dt

w.start()

# 获取期权合约信息OptionContractRawData
OptionContractNameRawData = w.wset("optioncontractbasicinfo", "exchange=sse;windcode=510050.SH;status=trading")
OptionContractNameData = pd.DataFrame(OptionContractNameRawData.Data).T
OptionContractNameData.columns = OptionContractNameRawData.Fields
OptionContractNameData['wind_code'] = OptionContractNameData['wind_code'].map(lambda x: str(x) + ".SH")
# 生成期权合约代码
OptionContractNameCode = ",".join(OptionContractNameData['wind_code'])
# 提取分钟级历史数据
OptionContractMinuteRawData = w.wsi(OptionContractNameCode,
                                    "open,high,low,close,volume,amt,chg,pct_chg,oi,begintime,endtime",
                                    "2019-10-30 09:00:00", "2019-10-31 18:25:00", "Fill=Previous;PriceAdj=F")
OptionContractMinuteData = pd.DataFrame(OptionContractMinuteRawData.Data).T
OptionContractMinuteData.columns = OptionContractMinuteRawData.Fields
# 增加分钟级数据的时间戳
OptionContractMinuteData['datetime'] = OptionContractMinuteRawData.Times
OptionContractMinuteData['recodedate'] = OptionContractMinuteData['datetime'].map(lambda x: x.strftime('%Y-%m-%d'))
OptionContractMinuteData['recodetime'] = OptionContractMinuteData['datetime'].map(lambda x: x.strftime('%H:%M:%S'))
