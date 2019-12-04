# __author:wtxhpx1991
# data:2019/12/4

import option
import pandas as pd
from WindPy import *

w.start()

START_DATE = "2019-01-01"
END_DATE = "2019-12-01"
# 获取期间挂牌交易过的期权合约代码
OptionContractSet = option.OptionContract.GetListedContractBetweenGivenDate(START_DATE, END_DATE)
OptionContractStr = list(OptionContractSet['wind_code'])
# 获取期权逐日成交量数据，并剔除空值
OptionContractRawDatavol = w.wsd(OptionContractStr, "volume", START_DATE, END_DATE, "PriceAdj=F")
OptionContractTempDatavol = pd.DataFrame(OptionContractRawDatavol.Data).T
OptionContractTempDatavol.index = OptionContractRawDatavol.Times
OptionContractTempDatavol.columns = OptionContractRawDatavol.Codes
OptionContractTempDatavol["datetime"] = OptionContractTempDatavol.index
OptionContractTempDatavol = pd.melt(OptionContractTempDatavol, id_vars="datetime", var_name="wind_code",
                                    value_name="volumn")
OptionContractDatavol = OptionContractTempDatavol.dropna()
OptionContractDatavol = OptionContractDatavol.reset_index()
OptionContractDatavol = OptionContractDatavol.drop(["index"], axis=1)
# 按三分钟的30%计算
OptionContractDatavol["vol3minutes"] = OptionContractDatavol["volumn"] / 80 * 0.3

# 计算期权合约前结算价
OptionContractRawDataClose = w.wsd(OptionContractStr, "pre_settle", START_DATE, END_DATE, "PriceAdj=F")
OptionContractTempDataClose = pd.DataFrame(OptionContractRawDataClose.Data).T
OptionContractTempDataClose.index = OptionContractRawDataClose.Times
OptionContractTempDataClose.columns = OptionContractRawDataClose.Codes
OptionContractTempDataClose["datetime"] = OptionContractTempDataClose.index
OptionContractTempDataClose = pd.melt(OptionContractTempDataClose, id_vars="datetime", var_name="wind_code",
                                      value_name="pre_settle")
OptionContractDataClose = OptionContractTempDataClose.dropna()
OptionContractDataClose = OptionContractDataClose.reset_index()
OptionContractDataClose = OptionContractDataClose.drop(["index"], axis=1)
# 将结算价合并到成交量上
OptionContractData = pd.merge(OptionContractDatavol, OptionContractDataClose, on=["datetime", "wind_code"], how="left")
OptionContractSetTemp = OptionContractSet[['wind_code', 'call_or_put', 'exercise_price', 'exercise_date']]
OptionContractSetTemp = OptionContractSetTemp.reset_index(drop=True)
OptionContractData = pd.merge(OptionContractData, OptionContractSetTemp, on="wind_code", how="left")
# 计算到期日
OptionContractData['datetimef'] = OptionContractData['datetime'].map(lambda x: x.strftime('%Y-%m-%d'))
OptionContractData["time"] = OptionContractData.apply(option.TradeCalendar.TradeDaysCountAnnualizedForApply, axis=1,
                                                      StartDate="datetimef",
                                                      EndDate="exercise_date")
OptionContractData["time"] = OptionContractData["time"] + 1 / 252

