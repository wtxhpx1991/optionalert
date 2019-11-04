from WindPy import *
import pandas as pd
import numpy as np
from scipy.stats import norm

import datetime as dt

w.start()
# 定义无风险利率以及股息率
RISK_FREE_INTEREST_RATE = 0.025
DIVIDEND_RATE = 0


# 欧式认购期权价格计算
def EuropeanCallPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
    dt = Volatility * (Time ** 0.5)
    d1 = np.log(UnderlyingPrice / ExercisePrice) + (InterestRate - DividendRate + 0.5 * (Volatility ** 2)) / dt
    d2 = d1 - dt
    nd1 = norm.cdf(d1)
    nd2 = norm.cdf(d2)
    result = np.exp(-DividendRate * Time) * UnderlyingPrice * nd1 - ExercisePrice * np.exp(-InterestRate * Time) * nd2
    return result


# 欧式认沽期权价格计算
def EuropeanPutPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
    dt = Volatility * (Time ** 0.5)
    d1 = np.log(UnderlyingPrice / ExercisePrice) + (InterestRate - DividendRate + 0.5 * (Volatility ** 2)) / dt
    d2 = d1 - dt
    nd1 = norm.cdf(-d1)
    nd2 = norm.cdf(-d2)
    result = ExercisePrice * np.exp(-InterestRate * Time) * nd2 - np.exp(-DividendRate * Time) * UnderlyingPrice * nd1
    return result


# 求解欧式认购期权隐含波动率

def ImpliedCallVolatility(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Target):
    HIGH = 5
    LOW = 0
    while (HIGH - LOW) > 0.00001:
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
    while (HIGH - LOW) > 0.00001:
        if EuropeanPutPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                            (HIGH + LOW) / 2) > Target:
            HIGH = (HIGH + LOW) / 2
        else:
            LOW = (HIGH + LOW) / 2
    return (HIGH + LOW) / 2


# 获取交易日间隔
def TradeDateInterval(ArrLike, StartDate, EndDate):
    '''
    调用wind函数，起始日期和截止日期使用"%Y-%m-%d"
    :param StartDate: "%Y-%m-%d"
    :param EndDate: "%Y-%m-%d"
    :return:
    '''
    return w.tdayscount(ArrLike[StartDate], ArrLike[EndDate], "TradingCalendar=SSE").Data[0][0]


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
OptionContractData['tradedateinverval'] = OptionContractData.apply(TradeDateInterval, axis=1, StartDate="recodedate",
                                                                   EndDate="exercise_date")
# # 检验数据是否正确
# OptionContractDataTest = OptionContractData.groupby(by=["limit_month", "exercise_price", "call_or_put"]).size()
# # 每个合约数据相同
# OptionContractDataTest.min() == OptionContractDataTest.max()
# # 每个合约都有认沽认购
# OptionContractDataTest.count(level='call_or_put')[0] == OptionContractDataTest.count(level='call_or_put')[1]
