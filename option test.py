from WindPy import *
import pandas as pd
import datetime as dt

w.start()
# 定义无风险利率以及股息率
RISK_FREE_RATE = 0.025
DIVIDEND_RATE = 0
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
# 生成分析数据
OptionContractData = pd.merge(OptionContractMinuteData, OptionContractNameData, left_on="windcode",
                              right_on="wind_code", how="left")
# 检验数据是否正确
OptionContractDataTest = OptionContractData.groupby(by=["limit_month", "exercise_price", "call_or_put"]).size()
# 每个合约数据相同
OptionContractDataTest.min() == OptionContractDataTest.max()
# 每个合约都有认沽认购
OptionContractDataTest.count(level='call_or_put')[0] == OptionContractDataTest.count(level='call_or_put')[1]
