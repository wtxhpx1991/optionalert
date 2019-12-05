# __author:wtxhpx1991
# data:2019/12/4

import option
import pandas as pd
import bisect
from WindPy import *

InterestRate = 0.025
DividendRate = 0.00
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
# 获取标的ETF数据
UnderlyingRawData = w.wsd("510050.SH", "pre_close", START_DATE, END_DATE, "Fill=Previous;PriceAdj=F")
UnderlyingTempData = pd.DataFrame(UnderlyingRawData.Data).T
UnderlyingTempData.columns = UnderlyingRawData.Fields
UnderlyingTempData['datetime'] = UnderlyingRawData.Times
OptionContractData = pd.merge(OptionContractData, UnderlyingTempData, on='datetime', how='left')
# 计算到期日
OptionContractData['datetimef'] = OptionContractData['datetime'].map(lambda x: x.strftime('%Y-%m-%d'))
OptionContractData['exercise_datef'] = OptionContractData['exercise_date'].map(
    lambda x: datetime.strptime(x, '%Y-%m-%d').date())
# def dayscount(arrlike, startdate, enddate):
#     return w.tdayscount(arrlike[startdate], arrlike[enddate], "").Data[0][0]
# aa = OptionContractData.head(100)
# aa.apply(dayscount, axis=1, startdate="datetimef", enddate="exercise_date")
# aa.apply(option.TradeCalendar.TradeDaysCountAnnualizedForApply, axis=1,
#          StartDate="datetimef",
#          EndDate="exercise_date")
# OptionContractData=OptionContractData.head(100)


# 获取交易日历
TradeCalendar = option.TradeCalendar.TradeCalendarStartToEnd(START_DATE, '2020-10-10')
OptionContractData_startdate = pd.DataFrame(OptionContractData['datetime'].drop_duplicates())


def startdateindex(arrlike, i):
    return bisect.bisect_left(TradeCalendar, arrlike[i])


OptionContractData_startdate['datetime_index'] = OptionContractData_startdate.apply(startdateindex, axis=1,
                                                                                    i="datetime")


def enddateindex(arrlike, i):
    return bisect.bisect_right(TradeCalendar, arrlike[i])


OptionContractData_enddate = pd.DataFrame(OptionContractData['exercise_datef'].drop_duplicates())
OptionContractData_enddate['exercise_datef_index'] = OptionContractData_enddate.apply(enddateindex, axis=1,
                                                                                      i="exercise_datef")

OptionContractData = pd.merge(OptionContractData, OptionContractData_startdate, on='datetime', how='left')
OptionContractData = pd.merge(OptionContractData, OptionContractData_enddate, on='exercise_datef', how='left')
OptionContractData['time'] = (OptionContractData['exercise_datef_index'] - OptionContractData['datetime_index']) / 252
OptionContractData["InterestRate"] = InterestRate
OptionContractData["DividendRate"] = DividendRate
OptionContractData['volatility'] = OptionContractData.apply(option.OptionGreeksMethod.ImpliedVolatilityForApply, axis=1,
                                                            Direction="call_or_put",
                                                            UnderlyingPrice="PRE_CLOSE",
                                                            ExercisePrice="exercise_price", Time="time",
                                                            InterestRate="InterestRate",
                                                            DividendRate="DividendRate",
                                                            Target="pre_settle")
OptionContractData['delta'] = OptionContractData.apply(option.OptionGreeksMethod.DeltaValueForApply, axis=1,
                                                       Direction="call_or_put",
                                                       UnderlyingPrice="PRE_CLOSE",
                                                       ExercisePrice="exercise_price", Time="time",
                                                       InterestRate="InterestRate",
                                                       DividendRate="DividendRate",
                                                       Volatility="volatility")

OptionContractData['deltaabs']=OptionContractData['delta'].map(abs)



OptionContractData['deltagroup']=pd.cut(OptionContractData['deltaabs'],10)
OptionContractData['timegroup']=pd.cut(OptionContractData['time'],10)
OptionContractData.plot('delta','vol3minutes',kind='scatter')
OptionContractData.plot('time','vol3minutes',kind='scatter')
OptionContractData[['vol3minutes','timegroup']].boxplot(by='timegroup')
OptionContractData[['vol3minutes','deltagroup']].boxplot(by='deltagroup')


from mpl_toolkits.mplot3d.axes3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
fig = plt.figure()
axes3d = Axes3D(fig)
c=OptionContractData['vol3minutes']
axes3d.scatter(OptionContractData['time'],OptionContractData['deltaabs'],OptionContractData['vol3minutes'],c=c,cmap=cm.Reds)
axes3d.set_xlabel('time')
axes3d.set_ylabel('deltaabs')
axes3d.set_zlabel('vol3minutes')