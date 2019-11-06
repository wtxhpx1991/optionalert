from WindPy import *
import pandas as pd
import numpy as np
from scipy.stats import norm
import datetime as dt

w.start()
# 定义无风险利率以及股息率
RISK_FREE_INTEREST_RATE = 0.025
DIVIDEND_RATE = 0
TRADE_CALENDAR = w.tdays("2018-01-01", "2020-12-31", "TradingCalendar=SZSE").Times


# 欧式认购期权价格计算
def EuropeanCallPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
    dt = Volatility * (Time ** 0.5)
    d1 = (np.log(UnderlyingPrice / ExercisePrice) + (InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
    d2 = d1 - dt
    nd1 = norm.cdf(d1)
    nd2 = norm.cdf(d2)
    result = np.exp(-DividendRate * Time) * UnderlyingPrice * nd1 - ExercisePrice * np.exp(-InterestRate * Time) * nd2
    return result


# 欧式认沽期权价格计算
def EuropeanPutPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
    dt = Volatility * (Time ** 0.5)
    d1 = (np.log(UnderlyingPrice / ExercisePrice) + (InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
    d2 = d1 - dt
    nd1 = norm.cdf(-d1)
    nd2 = norm.cdf(-d2)
    result = ExercisePrice * np.exp(-InterestRate * Time) * nd2 - np.exp(-DividendRate * Time) * UnderlyingPrice * nd1
    return result


# 求解欧式认购期权隐含波动率

def ImpliedCallVolatility(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Target):
    HIGH = 5
    LOW = 0
    while (HIGH - LOW) > 0.0001:
        if EuropeanCallPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                             (HIGH + LOW) / 2) > Target:
            HIGH = (HIGH + LOW) / 2
        else:
            LOW = (HIGH + LOW) / 2
    return (HIGH + LOW) / 2


# 求解欧式认沽期权隐含波动率
def ImpliedPutVolatility(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Target):
    HIGH = 5
    LOW = 0
    while (HIGH - LOW) > 0.0001:
        if EuropeanPutPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                            (HIGH + LOW) / 2) > Target:
            HIGH = (HIGH + LOW) / 2
        else:
            LOW = (HIGH + LOW) / 2
    return (HIGH + LOW) / 2


# 求解欧式期权隐含波动率
def ImpliedVolatility(ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Target):
    if ArrLike[Direction] == "认购":
        return ImpliedCallVolatility(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate], ArrLike[DividendRate], ArrLike[Target])
    else:
        return ImpliedPutVolatility(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                    ArrLike[InterestRate], ArrLike[DividendRate], ArrLike[Target])


# 获取交易日间隔
def TradeDateInterval(ArrLike, StartDate, EndDate):
    '''
    调用wind函数，起始日期和截止日期使用"%Y-%m-%d"
    :param StartDate: "%Y-%m-%d"
    :param EndDate: "%Y-%m-%d"
    :return:
    ！！！不要用wind的w.tdayscount("2019-11-04", "2019-11-04", "TradingCalendar=SZSE")函数，太慢了！！！
    '''
    StartDateFormat = dt.datetime.strptime(ArrLike[StartDate], "%Y-%m-%d").date()
    EndDateFormat = dt.datetime.strptime(ArrLike[EndDate], "%Y-%m-%d").date()
    return TRADE_CALENDAR.index(EndDateFormat) - TRADE_CALENDAR.index(StartDateFormat) + 1


# 获取期权合约信息OptionContractRawData
OptionContractNameRawData = w.wset("optioncontractbasicinfo", "exchange=sse;windcode=510050.SH;status=trading")
# # 全部合约w.wset("optioncontractbasicinfo","exchange=sse;windcode=510050.SH;status=all")
OptionContractNameData = pd.DataFrame(OptionContractNameRawData.Data).T
OptionContractNameData.columns = OptionContractNameRawData.Fields
OptionContractNameData['wind_code'] = OptionContractNameData['wind_code'].map(lambda x: str(x) + ".SH")
# 生成期权合约代码
OptionContractNameCode = ",".join(OptionContractNameData['wind_code'])
# 提取分钟级历史数据
OptionContractMinuteRawData = w.wsi(OptionContractNameCode,
                                    "open,high,low,close,volume,amt,chg,pct_chg,oi,begintime,endtime",
                                    "2019-10-31 09:00:00", "2019-10-31 18:00:00", "Fill=Previous;PriceAdj=F")
OptionContractMinuteData = pd.DataFrame(OptionContractMinuteRawData.Data).T
OptionContractMinuteData.columns = OptionContractMinuteRawData.Fields
# 增加分钟级数据的时间戳
OptionContractMinuteData['datetime'] = OptionContractMinuteRawData.Times
OptionContractMinuteData['recodedate'] = OptionContractMinuteData['datetime'].map(lambda x: x.strftime('%Y-%m-%d'))
OptionContractMinuteData['recodetime'] = OptionContractMinuteData['datetime'].map(lambda x: x.strftime('%H:%M:%S'))
# 生成分析数据
OptionContractData = pd.merge(OptionContractMinuteData, OptionContractNameData, left_on="windcode",
                              right_on="wind_code", how="left")
# 计算到期日
OptionContractData['tradedateinterval'] = OptionContractData.apply(TradeDateInterval, axis=1, StartDate="recodedate",
                                                                   EndDate="exercise_date")
OptionContractData['tradedateinterval'] = OptionContractData['tradedateinterval'] / 252
# # 检验数据是否正确
# OptionContractDataTest = OptionContractData.groupby(by=["limit_month", "exercise_price", "call_or_put"]).size()
# # 每个合约数据相同
# OptionContractDataTest.min() == OptionContractDataTest.max()
# # 每个合约都有认沽认购
# OptionContractDataTest.count(level='call_or_put')[0] == OptionContractDataTest.count(level='call_or_put')[1]
# 获取50etf分钟级数据
ETFMinuteRawData = w.wsi("510050.SH", "open,high,low,close,volume,amt,chg,pct_chg,oi,begintime,endtime",
                         "2019-10-31 09:00:00",
                         "2019-10-31 18:00:00", "Fill=Previous;PriceAdj=F")
ETFtMinuteData = pd.DataFrame(ETFMinuteRawData.Data).T
ETFtMinuteData.columns = ETFMinuteRawData.Fields
# 增加分钟级数据的时间戳
ETFtMinuteData['datetime'] = ETFMinuteRawData.Times
ETFtMinuteData['recodedate'] = OptionContractMinuteData['datetime'].map(lambda x: x.strftime('%Y-%m-%d'))
ETFtMinuteData['recodetime'] = OptionContractMinuteData['datetime'].map(lambda x: x.strftime('%H:%M:%S'))
# 重命名字段，增加50etf标识
ETFtMinuteData.columns = ["50ETF_" + str(x) for x in ETFtMinuteData.columns]
# 生成分析数据
OptionData = pd.merge(OptionContractData, ETFtMinuteData, left_on="datetime",
                      right_on="50ETF_datetime", how="left")
OptionData['interestrate'] = RISK_FREE_INTEREST_RATE
OptionData['dividendrate'] = DIVIDEND_RATE
# 计算隐含波动率
OptionData["ImpliedVolatility"] = OptionData.apply(ImpliedVolatility, axis=1, Direction="call_or_put",
                                                   UnderlyingPrice="50ETF_close",
                                                   ExercisePrice="exercise_price", Time="tradedateinterval",
                                                   InterestRate="interestrate",
                                                   DividendRate="dividendrate",
                                                   Target="close")

OptionData["ImpliedVolatility"].hist(bins=200)

