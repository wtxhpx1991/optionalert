# __author:wtxhpx1991


from WindPy import *
import pandas as pd
import numpy as np
from scipy.stats import norm
import datetime as dt
import matplotlib.pyplot as plt

plt.style.use('ggplot')
from mpl_toolkits.mplot3d import Axes3D

w.start()
global ContractSetData
global UnderlyingSecurity
global DividendRate
global InterestRate
UnderlyingSecurity = "510050.SH"
InterestRate = 0.025
DividendRate = 0.00


def ContractSet(exchange="sse", windcode=UnderlyingSecurity, status="all"):
    '''
    获取期权合约数据集，写在OptionContract类外面，赋值给全局变量ContractSetData，避免频繁调用w.wset函数。
    :return: 返回期权合约数据集，pandas.dataframe
    '''
    parameter = "exchange=" + exchange + ";" + "windcode=" + windcode + ";" + "status=" + status
    ExchangeLabel = "." + windcode.split(".")[1]  # 判断交易所标签，如"510050.SH"->".SH"
    OptionContractNameRawData = w.wset("optioncontractbasicinfo", parameter)
    OptionContractNameData = pd.DataFrame(OptionContractNameRawData.Data).T
    OptionContractNameData.columns = OptionContractNameRawData.Fields
    OptionContractNameData.index = OptionContractNameData['wind_code'].map(lambda x: str(x) + ExchangeLabel)
    OptionContractNameData['wind_code'] = OptionContractNameData['wind_code'].map(lambda x: str(x) + ExchangeLabel)
    return OptionContractNameData


ContractSetData = ContractSet()


class OptionContract:
    '''
    期权合约类
    ContractSet方法:使用wind接口获取上证50ETF全部合约，包括已经摘牌的合约。
    '''

    @classmethod
    def GetContractInformationByIndex(cls, wind_code):
        '''
        根据wind_code查询期权合约信息
        :param wind_code:
        :return: 返回期权合约信息，pandas.series
        '''
        return ContractSetData.loc[wind_code, :]

    @classmethod
    def GetListedContractOnGivenDate(cls, GivenDate):
        '''
        返回指定日期正挂牌交易的合约
        :param GivingDate:给定日期%Y-%m-%d
        :return:返回期权合约数据集，pandas.dataframe
        '''
        return ContractSetData[(ContractSetData["listed_date"] <= dt.datetime.strptime(GivenDate, "%Y-%m-%d")) & (
                ContractSetData["expire_date"] >= dt.datetime.strptime(GivenDate, "%Y-%m-%d"))]

    @classmethod
    def GetListedContractAfterGivenDate(cls, GivenDate):
        '''
        返回指定日期（含）之后曾挂牌交易过的合约，用于数据测算时提取数据使用。包含给定日期后挂牌现在已经摘牌的及仍在交易的。
        :param GivingDate:给定日期%Y-%m-%d
        :return:返回期权合约数据集，pandas.dataframe
        '''
        return ContractSetData[ContractSetData["listed_date"] >= dt.datetime.strptime(GivenDate, "%Y-%m-%d")]

    @classmethod
    def GetListedContractBetweenGivenDate(cls, StartDate, EndDate):
        '''
        返回指定日期之间曾挂牌交易过的合约，用于数据测算时提取数据使用。
        一共两种情形：一是挂牌早于起始时间，但摘牌晚于起始时间；二是挂牌在期间的。即期初正在交易的和期间挂牌交易的。
        :param StartDate:给定日期%Y-%m-%d
        :param EndDate: 给定日期%Y-%m-%d
        :return:返回期权合约数据集，pandas.dataframe
        '''
        ListedContractOnStartDate = cls.GetListedContractOnGivenDate(StartDate)
        ListedContractInTimeInterval = ContractSetData[
            (ContractSetData["listed_date"] > dt.datetime.strptime(StartDate, "%Y-%m-%d")) & (
                    ContractSetData["listed_date"] <= dt.datetime.strptime(EndDate, "%Y-%m-%d"))]
        return ListedContractOnStartDate.append(ListedContractInTimeInterval)

    @classmethod
    def GetVerticalContractByGivenDate(cls, wind_code, GivenDate):
        '''
        给定期权合约及指定日期，返回其垂直合约列表（包含本合约）。垂直合约是指同一到期月份不同执行价格的合约。
        :param wind_code:例如"10001504.SH"
        :param GivenDate:例如'2019-04-01'
        :return:
        '''
        ListedContractOnGivenDate = cls.GetListedContractOnGivenDate(GivenDate)
        if wind_code in list(ListedContractOnGivenDate.index):
            # 判断，如果合约在指定日期仍挂牌交易，返回该合约信息ContractInformationOnGivenDate，并基于该信息查询垂直合约列表
            ContractInformationOnGivenDate = ListedContractOnGivenDate.loc[wind_code, :]
            ContractLimitMonth = ContractInformationOnGivenDate['limit_month']  # 返回合约到期月份
            return ListedContractOnGivenDate[ListedContractOnGivenDate['limit_month'] == ContractLimitMonth]
        else:
            print("该合约在" + GivenDate + "已经摘牌")

    @classmethod
    def GetHorizonContractByGivenDate(cls, wind_code, GivenDate):
        '''
        给定期权合约及指定日期，返回其水平合约列表（包含本合约）。水平合约是指同执行价格一不同到期月份的合约。
        :param wind_code:例如"10001504.SH"
        :param GivenDate:例如'2019-04-01'
        :return:
        '''
        ListedContractOnGivenDate = cls.GetListedContractOnGivenDate(GivenDate)
        if wind_code in list(ListedContractOnGivenDate.index):
            # 判断，如果合约在指定日期仍挂牌交易，返回该合约信息ContractInformationOnGivenDate，并基于该信息查询水平合约列表
            ContractInformationOnGivenDate = ListedContractOnGivenDate.loc[wind_code, :]
            ContractExercisePrice = ContractInformationOnGivenDate['exercise_price']  # 返回合约执行价格
            return ListedContractOnGivenDate[ListedContractOnGivenDate['exercise_price'] == ContractExercisePrice]
        else:
            print("该合约在" + GivenDate + "已经摘牌")

    @classmethod
    def GetTTableContractByGivenDate(cls, wind_code, GivenDate):
        '''
        给定期权合约及指定日期，返回其T型合约列表（包含本合约）。
        :param wind_code:
        :param GivenDate:
        :return:
        '''
        ListedContractOnGivenDate = cls.GetListedContractOnGivenDate(GivenDate)
        if wind_code in list(ListedContractOnGivenDate.index):
            # 判断，如果合约在指定日期仍挂牌交易，返回该合约信息ContractInformationOnGivenDate，并基于该信息查询T型合约列表
            ContractInformationOnGivenDate = ListedContractOnGivenDate.loc[wind_code, :]
            ContractLimitMonth = ContractInformationOnGivenDate['limit_month']  # 返回合约到期月份
            ListedContractOnGivenDateResult = ListedContractOnGivenDate[
                ListedContractOnGivenDate['limit_month'] == ContractLimitMonth]
            ContractExercisePrice = ContractInformationOnGivenDate['exercise_price']  # 返回合约执行价格
            TempResult = pd.concat([ListedContractOnGivenDateResult, ListedContractOnGivenDate[
                ListedContractOnGivenDate['exercise_price'] == ContractExercisePrice]])
            return TempResult.drop_duplicates().sort_index()  # 去重并排序


class TradeCalendar:
    '''
    获取交易日历，包含以下几种方法：
    1-返回起始日期至终止日期的交易日历TradeCalendarStartToEnd
    2-返回给定日期前后一段时间的交易日历
    3-返回起始日期至终止日期的交易日天数
    '''

    # def __init__(self, StartDate, EndDate):
    #     '''
    #     使用wind接口获取交易日历
    #     :param StartDate: 起始日期%Y-%m-%d
    #     :param EndDate: 终止日期%Y-%m-%d
    #     '''
    #     self.StartDate = StartDate
    #     self.EndDate = EndDate
    #
    # # w.tdays("2018-01-01", "2020-12-31", "TradingCalendar=SZSE").Times
    # # dt.datetime.today().date().strftime('%Y-%m-%d')
    # @staticmethod
    # def DateInterVal(DateInterval=365):
    #     '''
    #     静态方法，初始化实例可返回以当前日向前后一段时间的实例
    #     :param DateInterval:日期，int格式
    #     :return:
    #     '''
    #     StartDate = dt.datetime.today().date() + dt.timedelta(days=-DateInterval)
    #     EndDate = dt.datetime.today().date() + dt.timedelta(days=DateInterval)
    #     StartDate = StartDate.strftime('%Y-%m-%d')
    #     EndDate = EndDate.strftime('%Y-%m-%d')
    #     return TradeCalendar(StartDate, EndDate)
    #
    # @property
    # def TradeCalendarData(self):
    #     '''
    #     定义属性，返回日历数据
    #     :return: 返回日历数据，list格式，每一个元素为datetime.date格式
    #     '''
    #     return w.tdays(self.StartDate, self.EndDate, "TradingCalendar=SZSE").Times
    # @classmethod
    # def IntervalDaysCount(cls):
    #     '''
    #
    #     :return:
    #     '''
    #     pass
    @classmethod
    def TradeCalendarStartToEnd(cls, StartDate, EndDate):
        '''
        输入起始日期和终止日期，获取期间交易日历
        :param StartDate:"%Y-%m-%d"
        :param EndDate:"%Y-%m-%d"
        :return:返回日历数据，list格式，每一个元素为datetime.date格式
        '''
        return w.tdays(StartDate, EndDate, "").Times

    @classmethod
    def TradeCalendarBeforeToAfter(cls, IntervalDays):
        '''
        输入自然日天数，输出今日前后IntervalDays的交易日历
        :param NaturalDays:
        :return:
        '''
        StartDate = dt.datetime.today().date() + dt.timedelta(days=-IntervalDays)
        EndDate = dt.datetime.today().date() + dt.timedelta(days=IntervalDays)
        StartDate = StartDate.strftime('%Y-%m-%d')
        EndDate = EndDate.strftime('%Y-%m-%d')
        return cls.TradeCalendarStartToEnd(StartDate, EndDate)

    @classmethod
    def TradeDaysCount(cls, StartDate, EndDate):
        '''
        计算起始日期至终止日期期间的交易日天数
        :param StartDate:
        :param EndDate:
        :return:
        '''
        trade_calendar = cls.TradeCalendarStartToEnd(StartDate, EndDate)
        StartDateFormat = dt.datetime.strptime(StartDate, "%Y-%m-%d").date()
        EndDateFormat = dt.datetime.strptime(EndDate, "%Y-%m-%d").date()
        try:
            StartDateIndex = trade_calendar.index(StartDateFormat)
            EndDateIndex = trade_calendar.index(EndDateFormat)
        except ValueError:
            for x in trade_calendar:
                if x >= dt.datetime.strptime(StartDate, "%Y-%m-%d").date():
                    StartDateIndex = trade_calendar.index(x)
                    break
            EndDateIndex = len(trade_calendar) - 1
        return EndDateIndex - StartDateIndex + 1

    @classmethod
    def TradeDaysCountForApply(cls, ArrLike, StartDate, EndDate):
        '''
        计算起始日期至终止日期期间的交易日天数
        :param ArrLike:
        :param StartDate:
        :param EndDate:
        :return:
        '''
        trade_calendar = cls.TradeCalendarStartToEnd(ArrLike[StartDate], ArrLike[EndDate])
        StartDateFormat = dt.datetime.strptime(ArrLike[StartDate], "%Y-%m-%d").date()
        EndDateFormat = dt.datetime.strptime(ArrLike[EndDate], "%Y-%m-%d").date()
        try:
            StartDateIndex = trade_calendar.index(StartDateFormat)
            EndDateIndex = trade_calendar.index(EndDateFormat)
        except ValueError:
            for x in trade_calendar:
                if x >= dt.datetime.strptime(ArrLike[StartDate], "%Y-%m-%d").date():
                    StartDateIndex = trade_calendar.index(x)
                    break
            EndDateIndex = len(trade_calendar) - 1
        return EndDateIndex - StartDateIndex + 1

    @classmethod
    def TradeDaysCountAnnualized(cls, StartDate, EndDate):
        '''
        计算起始日期至终止日期期间的交易日天数
        :param StartDate:
        :param EndDate:
        :return:
        '''
        return cls.TradeDaysCount(StartDate, EndDate) / 252

    @classmethod
    def TradeDaysCountAnnualizedForApply(cls, ArrLike, StartDate, EndDate):
        '''
        计算起始日期至终止日期期间的交易日天数
        :param ArrLike:
        :param StartDate:
        :param EndDate:
        :return:
        '''
        return cls.TradeDaysCount(ArrLike[StartDate], ArrLike[EndDate]) / 252


class OptionGreeksMethod:
    '''
    计算给定欧式期权合约数据，计算期权的希腊字母，包括以下几个类方法：
    1-看涨期权价格计算EuropeanCallPrice
    2-看跌期权价格计算EuropeanPutPrice
    3.1-看涨期权隐含波动率计算ImpliedCallVolatility
    3.2-看涨期权隐含波动率计算ImpliedCallVolatilityForApply
    4.1-看跌期权隐含波动率计算ImpliedPutVolatility
    4.2-看跌期权隐含波动率计算ImpliedPutVolatilityForApply
    5-期权隐含波动率计算（基于call_or_put字段）ImpliedVolatilityForApply
    6-DELTA计算DeltaValueForApply
    6.1-看涨期权CallDeltaValue
    6.2-看涨期权CallDeltaValueForApply
    6.3-看跌期权PutDeltaValue
    6.4-看跌期权PutDeltaValueForApply
    7-GAMMA计算GammaValueForApply
    7.1-看涨期权CallGammaValue
    7.2-看涨期权CallGammaValueForApply
    7.3-看跌期权PutGammaValue
    7.4-看跌期权PutGammaValueForApply
    8-VEGA计算VegaValueForApply
    8.1-看涨期权CallVegaValue
    8.2-看涨期权CallVegaValueForApply
    8.3-看跌期权PutVegaValue
    8.4-看跌期权PutVegaValueForApply
    9-THETA计算ThetaValueForApply
    9.1-看涨期权CallThetaValue
    9.2-看涨期权CallThetaValueForApply
    9.3-看跌期权PutThetaValue
    9.4-看跌期权PutThetaValueForApply
    10-RHO计算RhoValueForApply
    10.1-看涨期权CallRhoValue
    10.2-看涨期权CallRhoValueForApply
    10.3-看跌期权PutRhoValue
    10.4-看跌期权PutRhoValueForApply
    11-Vomma计算VommaValueForApply，c/sigma*sigma
    11.1-看涨期权CallVommaValue
    11.2-看涨期权CallVommaValueForApply
    11.3-看跌期权PutVommaValue
    11.4-看跌期权PutVommaValueForApply
    12-Vanna计算VannaValueForApply，c/sigma*s
    12.1-看涨期权CallVannaValue
    12.2-看涨期权CallVannaValueForApply
    12.3-看跌期权PutVannaValue
    12.4-看跌期权PutVannaValueForApply
    13-Charm计算CharmValueForApply，c/s*t
    13.1-看涨期权CallCharmValue
    13.2-看涨期权CallCharmValueForApply
    13.3-看跌期权PutCharmValue
    13.4-看跌期权PutCharmValueForApply
    14-Veta计算VetaValueForApply，c/t*sigma
    14.1-看涨期权CallVetaValue
    14.2-看涨期权CallVetaValueForApply
    14.3-看跌期权PutVetaValue
    14.4-看跌期权PutVetaValueForApply
    其中，XXXXForApply类函数增加了ArrLike参数，用于对pandas.dataframe格式数据使用apply方法；
    不带call或者put说明对看涨或者看跌期权都是一个样子的，不做区分，可以直接用来清洗数据。
    '''

    @classmethod
    def EuropeanCallPrice(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
        '''
        1-看涨期权价格计算EuropeanCallPrice
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1 = norm.cdf(d1)
        nd2 = norm.cdf(d2)
        result = np.exp(-DividendRate * Time) * UnderlyingPrice * nd1 - ExercisePrice * np.exp(
            -InterestRate * Time) * nd2
        return result

    @classmethod
    def EuropeanPutPrice(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
        '''
        2-看跌期权价格计算EuropeanPutPrice
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1 = norm.cdf(-d1)
        nd2 = norm.cdf(-d2)
        result = ExercisePrice * np.exp(-InterestRate * Time) * nd2 - np.exp(
            -DividendRate * Time) * UnderlyingPrice * nd1
        return result

    @classmethod
    def ImpliedCallVolatility(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Target):
        '''
        3.1-看涨期权隐含波动率计算ImpliedCallVolatility
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Target:
        :return:
        '''
        HIGH = 2
        LOW = 0.00001
        while (HIGH - LOW) > 0.0001:
            if cls.EuropeanCallPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                                     (HIGH + LOW) / 2) > Target:
                HIGH = (HIGH + LOW) / 2
            else:
                LOW = (HIGH + LOW) / 2
        return (HIGH + LOW) / 2

    @classmethod
    def ImpliedCallVolatilityForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                                      Target):
        '''
        3.2-看涨期权隐含波动率计算ImpliedCallVolatilityForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Target:
        :return:
        '''
        HIGH = 2
        LOW = 0.00001
        while (HIGH - LOW) > 0.0001:
            if cls.EuropeanCallPrice(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate], ArrLike[DividendRate],
                                     (HIGH + LOW) / 2) > ArrLike[Target]:
                HIGH = (HIGH + LOW) / 2
            else:
                LOW = (HIGH + LOW) / 2
        return (HIGH + LOW) / 2

    @classmethod
    def ImpliedPutVolatility(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Target):
        '''
        4.1-看跌期权隐含波动率计算ImpliedPutVolatility
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Target:
        :return:
        '''
        HIGH = 2
        LOW = 0.00001
        while (HIGH - LOW) > 0.0001:
            if cls.EuropeanPutPrice(UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                                    (HIGH + LOW) / 2) > Target:
                HIGH = (HIGH + LOW) / 2
            else:
                LOW = (HIGH + LOW) / 2
        return (HIGH + LOW) / 2

    @classmethod
    def ImpliedPutVolatilityForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                                     Target):
        '''
        4.2-看跌期权隐含波动率计算ImpliedPutVolatilityForApply
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Target:
        :return:
        '''
        HIGH = 2
        LOW = 0.00001
        while (HIGH - LOW) > 0.0001:
            if cls.EuropeanPutPrice(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                    ArrLike[InterestRate], ArrLike[DividendRate],
                                    (HIGH + LOW) / 2) > ArrLike[Target]:
                HIGH = (HIGH + LOW) / 2
            else:
                LOW = (HIGH + LOW) / 2
        return (HIGH + LOW) / 2

    @classmethod
    def ImpliedVolatilityForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate,
                                  DividendRate,
                                  Target):
        '''
        5-期权隐含波动率计算（基于call_or_put字段）ImpliedVolatilityForApply
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Target:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.ImpliedCallVolatility(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                             ArrLike[InterestRate], ArrLike[DividendRate], ArrLike[Target])
        else:
            return cls.ImpliedPutVolatility(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                            ArrLike[InterestRate], ArrLike[DividendRate], ArrLike[Target])

    @classmethod
    def CallDeltaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
        '''
        6.1-看涨期权CallDeltaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        nd1 = norm.cdf(d1)
        result = nd1
        return result

    @classmethod
    def CallDeltaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                               Volatility):
        '''
        6.2-看涨期权CallDeltaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        nd1 = norm.cdf(d1)
        result = nd1
        return result

    @classmethod
    def PutDeltaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
        '''
        6.3-看跌期权PutDeltaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        nd1 = norm.cdf(d1)
        result = nd1 - 1
        return result

    @classmethod
    def PutDeltaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                              Volatility):
        '''
        6.4-看跌期权PutDeltaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        nd1 = norm.cdf(d1)
        result = nd1 - 1
        return result

    @classmethod
    def DeltaValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                           Volatility):
        '''
        6-DELTA计算DeltaValueForApply
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallDeltaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                      ArrLike[InterestRate],
                                      ArrLike[DividendRate],
                                      ArrLike[Volatility])
        else:
            return cls.PutDeltaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate],
                                     ArrLike[DividendRate],
                                     ArrLike[Volatility])

    @classmethod
    def CallGammaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                       Volatility):
        '''
        7.1-看涨期权CallGammaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        nd1_partial = norm.pdf(d1)
        result = nd1_partial / (UnderlyingPrice * dt)
        return result

    @classmethod
    def CallGammaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                               Volatility):
        '''
        7.2-看涨期权CallGammaValueForApply
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        nd1_partial = norm.pdf(d1)
        result = nd1_partial / (ArrLike[UnderlyingPrice] * dt)
        return result

    @classmethod
    def PutGammaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                      Volatility):
        '''
        7.3-看跌期权PutGammaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        nd1_partial = norm.pdf(d1)
        result = nd1_partial / (UnderlyingPrice * dt)
        return result

    @classmethod
    def PutGammaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                              Volatility):
        '''
        7.4-看跌期权PutGammaValueForApply
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        nd1_partial = norm.pdf(d1)
        result = nd1_partial / (ArrLike[UnderlyingPrice] * dt)
        return result

    @classmethod
    def GammaValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                           Volatility):
        '''
        7-GAMMA计算GammaValueForApply
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallGammaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                      ArrLike[InterestRate],
                                      ArrLike[DividendRate],
                                      ArrLike[Volatility])
        else:
            return cls.PutGammaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate],
                                     ArrLike[DividendRate],
                                     ArrLike[Volatility])

    @classmethod
    def CallVegaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                      Volatility):
        '''
        8.1-看涨期权CallVegaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        result = UnderlyingPrice * norm.pdf(d1) * (Time ** 0.5)
        return result

    @classmethod
    def CallVegaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                              Volatility):
        '''
        8.2-看涨期权CallVegaValueForApply
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        result = ArrLike[UnderlyingPrice] * norm.pdf(d1) * (ArrLike[Time] ** 0.5)
        return result

    @classmethod
    def PutVegaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                     Volatility):
        '''
        8.3-看跌期权PutVegaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        result = UnderlyingPrice * norm.pdf(d1) * (Time ** 0.5)
        return result

    @classmethod
    def PutVegaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                             Volatility):
        '''
        8.4-看跌期权PutVegaValueForApply
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        result = ArrLike[UnderlyingPrice] * norm.pdf(d1) * (ArrLike[Time] ** 0.5)
        return result

    @classmethod
    def VegaValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                          Volatility):
        '''
        8-VEGA计算VegaValueForApply
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallVegaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate],
                                     ArrLike[DividendRate],
                                     ArrLike[Volatility])
        else:
            return cls.PutVegaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                    ArrLike[InterestRate],
                                    ArrLike[DividendRate],
                                    ArrLike[Volatility])

    @classmethod
    def CallThetaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                       Volatility):
        '''
        9.1-看涨期权CallThetaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        nd2 = norm.cdf(d2)
        result = -UnderlyingPrice * nd1_partial * Volatility / (
                2 * (Time ** 0.5)) - InterestRate * ExercisePrice * np.exp(-InterestRate * Time) * nd2
        return result

    @classmethod
    def CallThetaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                               Volatility):
        '''
        9.2-看涨期权CallThetaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        nd2 = norm.cdf(d2)
        result = -ArrLike[UnderlyingPrice] * nd1_partial * ArrLike[Volatility] / (
                2 * (ArrLike[Time] ** 0.5)) - ArrLike[InterestRate] * ArrLike[ExercisePrice] * np.exp(
            -ArrLike[InterestRate] * ArrLike[Time]) * nd2
        return result

    @classmethod
    def PutThetaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                      Volatility):
        '''
        9.3-看跌期权PutThetaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        nd2 = norm.cdf(d2)
        result = -UnderlyingPrice * nd1_partial * Volatility / (
                2 * (Time ** 0.5)) + InterestRate * ExercisePrice * np.exp(-InterestRate * Time) * nd2
        return result

    @classmethod
    def PutThetaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                              Volatility):
        '''
        9.4-看跌期权PutThetaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        nd2 = norm.cdf(d2)
        result = -ArrLike[UnderlyingPrice] * nd1_partial * ArrLike[Volatility] / (
                2 * (ArrLike[Time] ** 0.5)) + ArrLike[InterestRate] * ArrLike[ExercisePrice] * np.exp(
            -ArrLike[InterestRate] * ArrLike[Time]) * nd2
        return result

    @classmethod
    def ThetaValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                           Volatility):
        '''
        9-THETA计算ThetaValueForApply
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallThetaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                      ArrLike[InterestRate],
                                      ArrLike[DividendRate],
                                      ArrLike[Volatility])
        else:
            return cls.PutThetaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate],
                                     ArrLike[DividendRate],
                                     ArrLike[Volatility])

    @classmethod
    def CallRhoValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                     Volatility):
        '''
        10.1-看涨期权CallRhoValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd2 = norm.cdf(d2)
        result = ExercisePrice * Time * np.exp(-InterestRate * Time) * nd2
        return result

    @classmethod
    def CallRhoValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                             Volatility):
        '''
        10.2-看涨期权CallRhoValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd2 = norm.cdf(d2)
        result = ArrLike[ExercisePrice] * ArrLike[Time] * np.exp(-ArrLike[InterestRate] * ArrLike[Time]) * nd2
        return result

    @classmethod
    def PutRhoValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                    Volatility):
        '''
        10.3-看跌期权PutRhoValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd2 = norm.cdf(-d2)
        result = -ExercisePrice * Time * np.exp(-InterestRate * Time) * nd2
        return result

    @classmethod
    def PutRhoValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                            Volatility):
        '''
        10.4-看跌期权PutRhoValueForApply
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd2 = norm.cdf(-d2)
        result = -ArrLike[ExercisePrice] * ArrLike[Time] * np.exp(-ArrLike[InterestRate] * ArrLike[Time]) * nd2
        return result

    @classmethod
    def RhoValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                         Volatility):
        '''
        10-RHO计算RhoValueForApply
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallRhoValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                    ArrLike[InterestRate],
                                    ArrLike[DividendRate],
                                    ArrLike[Volatility])
        else:
            return cls.PutRhoValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                   ArrLike[InterestRate],
                                   ArrLike[DividendRate],
                                   ArrLike[Volatility])

    @classmethod
    def CallVommaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                       Volatility):
        '''
        11.1-看涨期权CallVommaValue
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = UnderlyingPrice * nd1_partial * (Time ** 0.5) * d1 * d2 / Volatility
        return result

    @classmethod
    def CallVommaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                               Volatility):
        '''
        11.2-看涨期权CallVommaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = ArrLike[UnderlyingPrice] * nd1_partial * (ArrLike[Time] ** 0.5) * d1 * d2 / ArrLike[Volatility]
        return result

    @classmethod
    def PutVommaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                      Volatility):
        '''
        11.3-看跌期权PutVommaValue
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = UnderlyingPrice * nd1_partial * (Time ** 0.5) * d1 * d2 / Volatility
        return result

    @classmethod
    def PutVommaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                              Volatility):
        '''
        11.4-看跌期权PutVommaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = ArrLike[UnderlyingPrice] * nd1_partial * (ArrLike[Time] ** 0.5) * d1 * d2 / ArrLike[Volatility]
        return result

    @classmethod
    def VommaValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                           Volatility):
        '''
        11-Vomma计算VommaValueForApply，c/sigma*sigma
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallVommaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                      ArrLike[InterestRate],
                                      ArrLike[DividendRate],
                                      ArrLike[Volatility])
        else:
            return cls.PutVommaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate],
                                     ArrLike[DividendRate],
                                     ArrLike[Volatility])

    @classmethod
    def CallVannaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                       Volatility):
        '''
        12.1-看涨期权CallVannaValue
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = -nd1_partial * d2 / Volatility
        return result

    @classmethod
    def CallVannaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                               Volatility):
        '''
        12.2-看涨期权CallVannaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = -nd1_partial * d2 / ArrLike[Volatility]
        return result

    @classmethod
    def PutVannaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                      Volatility):
        '''
        12.3-看跌期权PutVannaValue
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = -nd1_partial * d2 / Volatility
        return result

    @classmethod
    def PutVannaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                              Volatility):
        '''
        12.4-看跌期权PutVannaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = -nd1_partial * d2 / ArrLike[Volatility]
        return result

    @classmethod
    def VannaValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                           Volatility):
        '''
        12-Vanna计算VannaValueForApply，c/sigma*s
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallVannaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                      ArrLike[InterestRate],
                                      ArrLike[DividendRate],
                                      ArrLike[Volatility])
        else:
            return cls.PutVannaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate],
                                     ArrLike[DividendRate],
                                     ArrLike[Volatility])

    @classmethod
    def CallCharmValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                       Volatility):
        '''
        13.1-看涨期权CallCharmValue
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = -nd1_partial * (2 * InterestRate * Time - d2 * dt) / (2 * Time * dt)
        return result

    @classmethod
    def CallCharmValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                               Volatility):
        '''
        13.2-看涨期权CallCharmValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = -nd1_partial * (2 * ArrLike[InterestRate] * ArrLike[Time] - d2 * dt) / (2 * ArrLike[Time] * dt)
        return result

    @classmethod
    def PutCharmValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                      Volatility):
        '''
        13.3-看跌期权PutCharmValue
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = -nd1_partial * (2 * InterestRate * Time - d2 * dt) / (2 * Time * dt)
        return result

    @classmethod
    def PutCharmValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                              Volatility):
        '''
        13.4-看跌期权PutCharmValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = -nd1_partial * (2 * ArrLike[InterestRate] * ArrLike[Time] - d2 * dt) / (2 * ArrLike[Time] * dt)
        return result

    @classmethod
    def CharmValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                           Volatility):
        '''
        13-Charm计算CharmValueForApply，c/s*t
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallCharmValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                      ArrLike[InterestRate],
                                      ArrLike[DividendRate],
                                      ArrLike[Volatility])
        else:
            return cls.PutCharmValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate],
                                     ArrLike[DividendRate],
                                     ArrLike[Volatility])

    @classmethod
    def CallVetaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                      Volatility):
        '''
        14.1-看涨期权CallVetaValue
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = UnderlyingPrice * nd1_partial * (Time ** 0.5) * (InterestRate * d1 / dt - (1 + d1 * d2) / (2 * Time))
        return result

    @classmethod
    def CallVetaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                              Volatility):
        '''
        14.2-看涨期权CallVetaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = ArrLike[UnderlyingPrice] * nd1_partial * (ArrLike[Time] ** 0.5) * (
                ArrLike[InterestRate] * d1 / dt - (1 + d1 * d2) / (2 * ArrLike[Time]))
        return result

    @classmethod
    def PutVetaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                     Volatility):
        '''
        14.3-看跌期权PutVetaValue
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = Volatility * (Time ** 0.5)
        d1 = (np.log(UnderlyingPrice / ExercisePrice) + (
                InterestRate - DividendRate + 0.5 * (Volatility ** 2)) * Time) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = UnderlyingPrice * nd1_partial * (Time ** 0.5) * (InterestRate * d1 / dt - (1 + d1 * d2) / (2 * Time))
        return result

    @classmethod
    def PutVetaValueForApply(cls, ArrLike, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                             Volatility):
        '''
        14.4-看跌期权PutVetaValueForApply
        :param ArrLike:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        dt = ArrLike[Volatility] * (ArrLike[Time] ** 0.5)
        d1 = (np.log(ArrLike[UnderlyingPrice] / ArrLike[ExercisePrice]) + (
                ArrLike[InterestRate] - ArrLike[DividendRate] + 0.5 * (ArrLike[Volatility] ** 2)) * ArrLike[Time]) / dt
        d2 = d1 - dt
        nd1_partial = norm.pdf(d1)
        result = ArrLike[UnderlyingPrice] * nd1_partial * (ArrLike[Time] ** 0.5) * (
                ArrLike[InterestRate] * d1 / dt - (1 + d1 * d2) / (2 * ArrLike[Time]))
        return result

    @classmethod
    def VetaValueForApply(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                          Volatility):
        '''
        14-Veta计算VetaValueForApply，c/t*sigma
        :param ArrLike:
        :param Direction:
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        if ArrLike[Direction] == "认购":
            return cls.CallVetaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                     ArrLike[InterestRate],
                                     ArrLike[DividendRate],
                                     ArrLike[Volatility])
        else:
            return cls.PutVetaValue(ArrLike[UnderlyingPrice], ArrLike[ExercisePrice], ArrLike[Time],
                                    ArrLike[InterestRate],
                                    ArrLike[DividendRate],
                                    ArrLike[Volatility])


class OptionMinuteData(OptionContract, TradeCalendar, OptionGreeksMethod):
    '''
    分钟级交易数据类，通过wind接口导入分钟级行情数据，并做格式化处理
    1-获取起始日期至终止日期指定合约数据
    2-获取起始日期至终止日期所有曾挂牌交易过的合约数据
    3-获取起始日期至终止日期标的ETF交易数据
    4-匹配现货标的交易数据
    5-计算greeks，默认计算Delta,Gamma,Vega,Theta,Rho。其余的Vomma,Vanna,Charm,Veta自行修改代码既可。
    '''

    # OptionContract.ContractSet()[OptionContract.ContractSet()['contract_state'] == "上市"].index
    # OptionContractMinuteData.DateInterVal(365).TradeCalendarData
    @classmethod
    def GetRawDataForGivenContract(cls, WindCode, StartDateTime, EndDateTime):
        '''
        1-获取起始日期至终止日期指定合约数据
        有个坑，wind接口中，如果windcode只有一个合约，是没有windcode这个字段的
        :param WindCode:
        :param StartDateTime:%Y-%m-%d %H:%M:%S
        :param EndDateTime:%Y-%m-%d %H:%M:%S
        :return:
        '''
        if len(WindCode.split(",")) == 1:
            OptionContractMinuteRawData = w.wsi(WindCode,
                                                "open,high,low,close,volume,amt,chg,pct_chg,oi",
                                                StartDateTime, EndDateTime, "Fill=Previous;PriceAdj=F")
            OptionContractMinuteData = pd.DataFrame(OptionContractMinuteRawData.Data).T
            OptionContractMinuteData.columns = OptionContractMinuteRawData.Fields
            OptionContractMinuteData.insert(0, 'windcode', OptionContractMinuteRawData.Codes[0])
            OptionContractMinuteData['datetime'] = OptionContractMinuteRawData.Times
            OptionContractMinuteData['date'] = OptionContractMinuteData['datetime'].dt.date
            OptionContractMinuteData['time'] = OptionContractMinuteData['datetime'].dt.time
        else:
            OptionContractMinuteRawData = w.wsi(WindCode,
                                                "open,high,low,close,volume,amt,chg,pct_chg,oi",
                                                StartDateTime, EndDateTime, "Fill=Previous;PriceAdj=F")
            OptionContractMinuteData = pd.DataFrame(OptionContractMinuteRawData.Data).T
            OptionContractMinuteData.columns = OptionContractMinuteRawData.Fields
            OptionContractMinuteData['datetime'] = OptionContractMinuteRawData.Times
            OptionContractMinuteData['date'] = OptionContractMinuteData['datetime'].dt.date
            OptionContractMinuteData['time'] = OptionContractMinuteData['datetime'].dt.time
        return OptionContractMinuteData

    @classmethod
    def GetRawDataForListedContract(cls, StartDateTime, EndDateTime):
        '''
        2-获取起始日期至终止日期所有曾挂牌交易过的合约数据
        :param StartDateTime:%Y-%m-%d %H:%M:%S
        :param EndDateTime:%Y-%m-%d %H:%M:%S
        :return:
        '''
        # dt.datetime.strptime(StartDateTime, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
        StartDate = StartDateTime.split(" ")[0]
        EndDate = EndDateTime.split(" ")[0]
        ContractSetBetweenStartAndEnd = list(cls.GetListedContractBetweenGivenDate(StartDate, EndDate).index)
        return cls.GetRawDataForGivenContract(",".join(ContractSetBetweenStartAndEnd), StartDateTime, EndDateTime)

    @classmethod
    def GetRawDataForUnderlyingSecurity(cls, StartDateTime, EndDateTime):
        '''
        3-获取起始日期至终止日期标的ETF交易数据
        :param StartDateTime:
        :param EndDateTime:
        :return:
        '''
        UnderlyingSecurityMinuteRawData = w.wsi(UnderlyingSecurity,
                                                "open,high,low,close,volume,amt,chg,pct_chg",
                                                StartDateTime, EndDateTime, "Fill=Previous;PriceAdj=F")
        UnderlyingSecurityMinuteData = pd.DataFrame(UnderlyingSecurityMinuteRawData.Data).T
        UnderlyingSecurityMinuteData.columns = UnderlyingSecurityMinuteRawData.Fields
        UnderlyingSecurityMinuteData.insert(0, 'windcode', UnderlyingSecurityMinuteRawData.Codes[0])
        UnderlyingSecurityMinuteData['datetime'] = UnderlyingSecurityMinuteRawData.Times
        UnderlyingSecurityMinuteData['date'] = UnderlyingSecurityMinuteData['datetime'].dt.date
        UnderlyingSecurityMinuteData['time'] = UnderlyingSecurityMinuteData['datetime'].dt.time
        return UnderlyingSecurityMinuteData

    @classmethod
    def GetDataForGivenContractAndUnderlyingSecurity(cls, WindCode, StartDateTime, EndDateTime):
        '''
        4.1-匹配现货标的交易数据
        :param WindCode:
        :param StartDateTime:
        :param EndDateTime:
        :return:
        '''

        RawDataForListedContract = cls.GetRawDataForGivenContract(WindCode, StartDateTime, EndDateTime)
        RawDataForUnderlyingSecurity = cls.GetRawDataForUnderlyingSecurity(StartDateTime, EndDateTime)
        OptionContractDataTemp = pd.merge(RawDataForListedContract, RawDataForUnderlyingSecurity, left_on="datetime",
                                          right_on="datetime", how="left", suffixes=("_op", "_etf"))
        OptionContractData = pd.merge(OptionContractDataTemp, ContractSetData, left_on="windcode_op",
                                      right_index=True, how="left")

        OptionContractData['StartDate'] = OptionContractData["date_op"].map(lambda x: x.strftime('%Y-%m-%d'))
        # OptionContractData["time_to_exercise"] = OptionContractData.apply(cls.TradeDaysCountAnnualizedForApply, axis=1,
        #                                                                   StartDate="StartDate", EndDate="exercise_date")
        # 直接这么算到期时间效率太低
        # 考虑去重，先针对不同合约不同交易日和不同到期日，实际上，同一天挂牌交易的同一个合约，其逐笔数据的到期交易日都是定的
        IntervalTempTable1 = OptionContractData[["windcode_op", "StartDate", "exercise_date"]].drop_duplicates()
        IntervalTempTable2 = OptionContractData[["StartDate", "exercise_date"]].drop_duplicates()
        IntervalTempTable2["time_to_exercise"] = IntervalTempTable2.apply(
            OptionMinuteData.TradeDaysCountAnnualizedForApply,
            axis=1,
            StartDate="StartDate", EndDate="exercise_date")
        IntervalTempTable13 = pd.merge(IntervalTempTable1, IntervalTempTable2, on=["StartDate", "exercise_date"],
                                       how="left")
        OptionContractData = pd.merge(OptionContractData, IntervalTempTable13,
                                      on=["windcode_op", "StartDate", "exercise_date"], how="left")

        OptionContractData["InterestRate"] = InterestRate
        OptionContractData["DividendRate"] = DividendRate
        return OptionContractData

    @classmethod
    def GetDataForListedContractAndUnderlyingSecurity(cls, StartDateTime, EndDateTime):
        '''
        4.2-匹配现货标的交易数据
        :param StartDateTime:
        :param EndDateTime:
        :return:
        '''
        RawDataForListedContract = cls.GetRawDataForListedContract(StartDateTime, EndDateTime)
        RawDataForUnderlyingSecurity = cls.GetRawDataForUnderlyingSecurity(StartDateTime, EndDateTime)
        OptionContractDataTemp = pd.merge(RawDataForListedContract, RawDataForUnderlyingSecurity, left_on="datetime",
                                          right_on="datetime", how="left", suffixes=("_op", "_etf"))
        OptionContractData = pd.merge(OptionContractDataTemp, ContractSetData, left_on="windcode_op",
                                      right_index=True, how="left")

        OptionContractData['StartDate'] = OptionContractData["date_op"].map(lambda x: x.strftime('%Y-%m-%d'))
        # OptionContractData["time_to_exercise"] = OptionContractData.apply(cls.TradeDaysCountAnnualizedForApply, axis=1,
        #                                                                   StartDate="StartDate", EndDate="exercise_date")
        # 直接这么算到期时间效率太低
        # 考虑去重，先针对不同合约不同交易日和不同到期日，实际上，同一天挂牌交易的同一个合约，其逐笔数据的到期交易日都是定的
        IntervalTempTable1 = OptionContractData[["windcode_op", "StartDate", "exercise_date"]].drop_duplicates()
        IntervalTempTable2 = OptionContractData[["StartDate", "exercise_date"]].drop_duplicates()
        IntervalTempTable2["time_to_exercise"] = IntervalTempTable2.apply(
            OptionMinuteData.TradeDaysCountAnnualizedForApply,
            axis=1,
            StartDate="StartDate", EndDate="exercise_date")
        IntervalTempTable13 = pd.merge(IntervalTempTable1, IntervalTempTable2, on=["StartDate", "exercise_date"],
                                       how="left")
        OptionContractData = pd.merge(OptionContractData, IntervalTempTable13,
                                      on=["windcode_op", "StartDate", "exercise_date"], how="left")

        OptionContractData["InterestRate"] = InterestRate
        OptionContractData["DividendRate"] = DividendRate
        return OptionContractData

    @classmethod
    def ComputeGreeksForListedContract(cls, DataSetForCompute):
        '''
        给出数据计算greeks，默认计算ImpliedVolatility,Delta,Gamma,Vega,Theta,Rho。
        :param DataForCompute: 数据集，pd.DataFrame，字段为wind格式，由GetDataForListedContractAndUnderlyingSecurity生成
        :return:
        '''
        DataSetForCompute["ImpliedVolatility"] = DataSetForCompute.apply(cls.ImpliedVolatilityForApply, axis=1,
                                                                         Direction="call_or_put",
                                                                         UnderlyingPrice="close_etf",
                                                                         ExercisePrice="exercise_price",
                                                                         Time="time_to_exercise",
                                                                         InterestRate="InterestRate",
                                                                         DividendRate="DividendRate",
                                                                         Target="close_op")
        DataSetForCompute["Delta"] = DataSetForCompute.apply(cls.DeltaValueForApply, axis=1, Direction="call_or_put",
                                                             UnderlyingPrice="close_etf",
                                                             ExercisePrice="exercise_price", Time="time_to_exercise",
                                                             InterestRate="InterestRate",
                                                             DividendRate="DividendRate",
                                                             Volatility="ImpliedVolatility")
        DataSetForCompute["Gamma"] = DataSetForCompute.apply(cls.GammaValueForApply, axis=1, Direction="call_or_put",
                                                             UnderlyingPrice="close_etf",
                                                             ExercisePrice="exercise_price", Time="time_to_exercise",
                                                             InterestRate="InterestRate",
                                                             DividendRate="DividendRate",
                                                             Volatility="ImpliedVolatility")
        DataSetForCompute["Vega"] = DataSetForCompute.apply(cls.VegaValueForApply, axis=1, Direction="call_or_put",
                                                            UnderlyingPrice="close_etf",
                                                            ExercisePrice="exercise_price", Time="time_to_exercise",
                                                            InterestRate="InterestRate",
                                                            DividendRate="DividendRate",
                                                            Volatility="ImpliedVolatility")
        DataSetForCompute["Theta"] = DataSetForCompute.apply(cls.ThetaValueForApply, axis=1, Direction="call_or_put",
                                                             UnderlyingPrice="close_etf",
                                                             ExercisePrice="exercise_price", Time="time_to_exercise",
                                                             InterestRate="InterestRate",
                                                             DividendRate="DividendRate",
                                                             Volatility="ImpliedVolatility")
        DataSetForCompute["Rho"] = DataSetForCompute.apply(cls.RhoValueForApply, axis=1, Direction="call_or_put",
                                                           UnderlyingPrice="close_etf",
                                                           ExercisePrice="exercise_price", Time="time_to_exercise",
                                                           InterestRate="InterestRate",
                                                           DividendRate="DividendRate",
                                                           Volatility="ImpliedVolatility")
        return DataSetForCompute


class OptionHistoryAlertForMinuteData:
    '''
    *期权报警类，包含滚动报警和刷新报警，用于历史数据回测。由于使用的是分钟级数据，报警的刷新频率默认1分钟，不做改动，对于滚动报警还增加窗宽参数。
    *该类初始化的时候需要填写数据源的起始时间和终止时间StartDateTime/EndDateTime，用于通过OptionMinuteData类的接口获取原始数据及GREEKS数据
    *刷新报警类关键字:RefreshAlert，滚动报警类关键字:RollAlert
    *初始化，得到原始数据及GREEKS数据，用于回测报警
    1-滚动报警类
    1.1-平价关系偏离RollAlert_OptionParityDeviate
    1.1.1-平价关系偏离原始数据RollAlert_OptionParityDeviate_RawData
    1.1.2-平价关系偏离测算结果RollAlert_OptionParityDeviate_Result
    1.2-隐含波动率瞬间偏离RollAlert_ImpliedVolatilityDeviate
    1.2.1-隐含波动率瞬间偏离原始数据RollAlert_ImpliedVolatilityDeviate_RawData
    1.2.2-隐含波动率瞬间偏离测算结果RollAlert_ImpliedVolatilityDeviate_Result
    1.3-价格瞬间偏离RollAlert_OptionPriceDeviate
    1.3.1-价格瞬间偏离原始数据RollAlert_OptionPriceDeviate_RawData
    1.3.2-价格瞬间偏离测算结果RollAlert_OptionPriceDeviate_Result
    2-刷新报警类
    ……
    '''

    def __init__(self, StartDateTime, EndDateTime):
        '''
        初始化类，得到合约交易数据和测算数据（含有希腊字母的）
        :param StartDateTime:"%Y-%m-%d %H:%M:%S"
        :param EndDateTime: "%Y-%m-%d %H:%M:%S"
        '''
        self.StartTime = StartDateTime
        self.EndTime = EndDateTime
        self.ListedContractData = OptionMinuteData.GetDataForListedContractAndUnderlyingSecurity(self.StartTime,
                                                                                                 self.EndTime)
        self.ListedContractDataWithGreeks = OptionMinuteData.ComputeGreeksForListedContract(self.ListedContractData)

    # todo 把数据格式处理成方便计算平价关系
    def FormatDataToParityCompute(self):
        '''
        关键字段，limit_month,exercise_price,datetime是主键
        认购期权和认沽期权不同的字段:
        'windcode_op', 'open_op', 'high_op', 'low_op', 'close_op', 'volume_op',
        'amount_op', 'change_op', 'pctchange_op', 'position','date_op', 'time_op',
        'wind_code', 'trade_code', 'sec_name',
        'call_or_put', 'listed_date',
        'expire_date', 'exercise_date', 'settlement_date', 'reference_price',
        'StartDate',  'ImpliedVolatility', 'Delta', 'Gamma',
        'Vega', 'Theta', 'Rho'
        认购期权和认沽期权相同的字段：
        'windcode_etf', 'open_etf', 'high_etf', 'low_etf',
        'close_etf', 'volume_etf', 'amount_etf', 'change_etf', 'pctchange_etf',
        'date_etf', 'time_etf'
        :return:
        '''
        TempResult = self.ListedContractDataWithGreeks
        TempCallResult = TempResult[TempResult["call_or_put"] == "认购"]
        TempPutResult = TempResult[TempResult["call_or_put"] == "认沽"].drop(
            columns=['windcode_etf', 'open_etf', 'high_etf', 'low_etf',
                     'close_etf', 'volume_etf', 'amount_etf', 'change_etf', 'pctchange_etf',
                     'date_etf', 'time_etf', 'option_mark_code', 'option_type', 'exercise_mode', 'contract_unit',
                     'settle_mode', 'contract_state', 'time_to_exercise',
                     'InterestRate', 'DividendRate'])
        result = pd.merge(TempCallResult, TempPutResult, how="left", on=["datetime", "limit_month", "exercise_price"],
                          suffixes=("_call", "_put"))
        return result

    def RollAlert_OptionParityDeviate_RawData(self):
        '''
        1.1.1-平价关系偏离原始数据RollAlert_OptionParityDeviate_RawData
        计算平价关系偏离报警的原始数据，包括正向平价比、反向平价比、多空隐含波动率比三个值
        :return:返回正向平价比、反向平价比、多空隐含波动率比
        '''
        TempResult = self.FormatDataToParityCompute()
        TempResult["Forward_Parity_Ratio"] = (TempResult["close_op_call"] + TempResult["exercise_price"] * (
                TempResult["time_to_exercise"] * TempResult["InterestRate"]).apply(lambda x: np.exp(-x))) / (
                                                     TempResult["close_op_put"] + TempResult["close_etf"]) - 1
        TempResult["Backward_Parity_Ratio"] = (TempResult["close_op_put"] + TempResult["close_etf"]) / (
                TempResult["close_op_call"] + TempResult["exercise_price"] * (
                TempResult["time_to_exercise"] * TempResult[
            "InterestRate"]).apply(lambda x: np.exp(-x))) - 1
        TempResult["Call_Put_ImpliedVolatility_Ratio"] = TempResult["ImpliedVolatility_call"] / TempResult[
            "ImpliedVolatility_put"] - 1
        return TempResult

    # CC = OptionHistoryAlertForMinuteData(StartDateTime, EndDateTime)
    # DD = CC.RollAlert_OptionParityDeviate_RawData()
    # DD_result = CC.RollAlert_OptionParityDeviate_Result(DD, 0.1, 0.1, 0.2)
    # DD_result.plot(x="Delta", y="ImpliedVolatilityDeviateRatio", kind="scatter")
    @classmethod
    def RollAlert_OptionParityDeviate_Result(cls, ArrLike, Arg1_Value, Arg2_Value, Arg3_Value):
        '''
        1.1.2-平价关系偏离测算结果RollAlert_OptionParityDeviate_Result
        :param ArrLike:
        :param Arg1_Value:
        :param Arg2_Value:
        :param Arg3_Value:
        :return:
        '''
        TempResult = ArrLike[
            (ArrLike["Forward_Parity_Ratio"] >= Arg1_Value) | (ArrLike["Backward_Parity_Ratio"] >= Arg2_Value) | (
                    ArrLike["Call_Put_ImpliedVolatility_Ratio"] >= Arg3_Value)]
        return TempResult[
            (TempResult["ImpliedVolatility_call"] >= 0.0001) & (TempResult["ImpliedVolatility_put"] >= 0.0001)]

    def RollAlert_ImpliedVolatilityDeviate_RawData(self, bandwith=3):
        '''
        1.2.1-隐含波动率瞬间偏离原始数据RollAlert_ImpliedVolatilityDeviate_RawData
        :param bandwith: 滚动区间，默认3min
        :return:
        '''
        result = self.ListedContractDataWithGreeks
        result["date_op_str"] = result["date_op"].apply(lambda x: x.strftime('%Y-%m-%d'))
        result["time_op_str"] = result["time_op"].apply(lambda x: x.strftime('%H:%M:%S'))
        # 计算rolling最大值
        result_groupby = result.groupby(["windcode_op", "date_op_str"])["time_op_str", "ImpliedVolatility"]
        result_groupby_max = result_groupby.rolling(bandwith, on="time_op_str").max()
        result_groupby_max = result_groupby_max.reset_index()
        result_groupby_max = result_groupby_max.drop(columns=["level_2"])
        result_groupby_max.rename(columns={"ImpliedVolatility": "ImpliedVolatility_Rolling_Max"}, inplace=True)
        result = pd.merge(result, result_groupby_max, how="left", on=["windcode_op", "date_op_str", "time_op_str"])
        # 计算rolling最小值
        result_groupby_min = result_groupby.rolling(bandwith, on="time_op_str").min()
        result_groupby_min = result_groupby_min.reset_index()
        result_groupby_min = result_groupby_min.drop(columns=["level_2"])
        result_groupby_min.rename(columns={"ImpliedVolatility": "ImpliedVolatility_Rolling_Min"}, inplace=True)
        result = pd.merge(result, result_groupby_min, how="left", on=["windcode_op", "date_op_str", "time_op_str"])
        result["ImpliedVolatility_Rolling_Max"] = result["ImpliedVolatility_Rolling_Max"].fillna(-9999)
        result["ImpliedVolatility_Rolling_Min"] = result["ImpliedVolatility_Rolling_Min"].fillna(-9999)
        result["ImpliedVolatilityDeviateRatio"] = result["ImpliedVolatility_Rolling_Max"] / result[
            "ImpliedVolatility_Rolling_Min"] - 1
        result["ImpliedVolatilityDeviateRatio"] = result["ImpliedVolatilityDeviateRatio"].abs()
        return result

    # CC = OptionHistoryAlertForMinuteData(StartDateTime, EndDateTime)
    # DD = CC.RollAlert_ImpliedVolatilityDeviate_RawData(bandwith=3)
    # DD_result = CC.RollAlert_ImpliedVolatilityDeviate_Result(DD, 0.0001)
    @classmethod
    def RollAlert_ImpliedVolatilityDeviate_Result(cls, ArrLike, Arg1_Value):
        '''
        1.2.2-隐含波动率瞬间偏离测算结果RollAlert_ImpliedVolatilityDeviate_Result
        :param ArrLike:
        :param Arg1_Value:
        :return:
        '''
        TempResult = ArrLike[ArrLike["ImpliedVolatilityDeviateRatio"] >= Arg1_Value]
        return TempResult[
            (TempResult["ImpliedVolatility_Rolling_Max"] >= 0.0001) & (
                    TempResult["ImpliedVolatility_Rolling_Min"] >= 0.0001)]

    def RollAlert_OptionPriceDeviate_RawData(self, bandwith=3):
        '''
        1.3.1-价格瞬间偏离原始数据RollAlert_OptionPriceDeviate_RawData
        :param bandwith: 滚动区间，默认3min
        :return:
        '''
        result = self.ListedContractDataWithGreeks
        result["date_op_str"] = result["date_op"].apply(lambda x: x.strftime('%Y-%m-%d'))
        result["time_op_str"] = result["time_op"].apply(lambda x: x.strftime('%H:%M:%S'))
        # 计算rolling最大值
        result_groupby = result.groupby(["windcode_op", "date_op_str"])["time_op_str", "close_op"]
        result_groupby_max = result_groupby.rolling(bandwith, on="time_op_str").max()
        result_groupby_max = result_groupby_max.reset_index()
        result_groupby_max = result_groupby_max.drop(columns=["level_2"])
        result_groupby_max.rename(columns={"close_op": "close_op_Rolling_Max"}, inplace=True)
        result = pd.merge(result, result_groupby_max, how="left", on=["windcode_op", "date_op_str", "time_op_str"])
        # 计算rolling最小值
        result_groupby_min = result_groupby.rolling(bandwith, on="time_op_str").min()
        result_groupby_min = result_groupby_min.reset_index()
        result_groupby_min = result_groupby_min.drop(columns=["level_2"])
        result_groupby_min.rename(columns={"close_op": "close_op_Rolling_Min"}, inplace=True)
        result = pd.merge(result, result_groupby_min, how="left", on=["windcode_op", "date_op_str", "time_op_str"])
        result["close_op_Rolling_Max"] = result["close_op_Rolling_Max"].fillna(-9999)
        result["close_op_Rolling_Min"] = result["close_op_Rolling_Min"].fillna(-9999)
        result["OptionPriceDeviateRatio"] = result["close_op_Rolling_Max"] / result[
            "close_op_Rolling_Min"] - 1
        result["OptionPriceDeviateRatio"] = result["OptionPriceDeviateRatio"].abs()
        return result

    @classmethod
    def RollAlert_OptionPriceDeviate_Resultt(cls, ArrLike, Arg1_Value):
        '''
        1.3.2-价格瞬间偏离测算结果RollAlert_OptionPriceDeviate_Result
        :param ArrLike:
        :param Arg1_Value:
        :return:
        '''
        TempResult = ArrLike[ArrLike["OptionPriceDeviateRatio"] >= Arg1_Value]
        # 不剔除算不出隐含波动率的
        # Result= TempResult[
        #     (TempResult["ImpliedVolatility_Rolling_Max"] >= 0.0001) & (
        #                 TempResult["ImpliedVolatility_Rolling_Min"] >= 0.0001)]
        # 剔除10tick以内的
        Result = TempResult[
            (TempResult["close_op_Rolling_Max"] -
             TempResult["close_op_Rolling_Min"]) >= 0.001]
        return Result


# todo 期权报警测算类，基于不同的参数阈值回测进行敏感性分析
class OptionHistoryAlertMeasure(OptionHistoryAlertForMinuteData):
    '''
    报警回测，进行敏感性分析
    '''
    pass


# todo 画图
class OptionPlot:
    '''
    期权图形
    1-隐含波动率曲面
    '''

    @staticmethod
    def ImpliedVolatilitySurfacePlot(GivenDateTime, Direction="认购"):
        '''
        画给定时刻50ETF隐含波动率曲面
        :param GivenDateTime:'%Y-%m-%d %H:%M:%S'
        :return:隐含波动率曲面
        '''
        StartDateTime = GivenDateTime
        EndDateTime = dt.datetime.strptime(GivenDateTime, '%Y-%m-%d %H:%M:%S') + dt.timedelta(seconds=1)
        EndDateTime = EndDateTime.strftime('%Y-%m-%d %H:%M:%S')
        OptionRawData = OptionMinuteData.GetDataForListedContractAndUnderlyingSecurity(StartDateTime, EndDateTime)
        OptionRawData = OptionMinuteData.ComputeGreeksForListedContract(OptionRawData)
        OptionDataForPlot = OptionRawData[OptionRawData["call_or_put"] == Direction]
        OptionDataForPlot_LimitMonth = OptionDataForPlot["limit_month"].drop_duplicates().sort_values()
        OptionDataForPlot_ExercisePrice = OptionDataForPlot["exercise_price"].drop_duplicates().sort_values()
        # 画隐含波动率曲面
        # 画出rsi与pct的相关系数曲面
        OptionDataForPlot_LimitMonth_Range = np.arange(len(OptionDataForPlot_LimitMonth))
        OptionDataForPlo_ExercisePrice_Range = np.arange(len(OptionDataForPlot_ExercisePrice))
        ImpliedVolatilitySurfacePlot_Array = np.empty(
            [len(OptionDataForPlot_ExercisePrice), len(OptionDataForPlot_LimitMonth)])
        OptionDataForPlot_LimitMonth_Range, OptionDataForPlo_ExercisePrice_Range = np.meshgrid(
            OptionDataForPlot_LimitMonth_Range, OptionDataForPlo_ExercisePrice_Range)
        for i in range(len(OptionDataForPlot_ExercisePrice)):
            for j in range(len(OptionDataForPlot_LimitMonth)):
                temp = OptionDataForPlot[
                    (OptionDataForPlot["limit_month"] == OptionDataForPlot_LimitMonth.iloc[j]) & (
                            OptionDataForPlot["exercise_price"] == OptionDataForPlot_ExercisePrice.iloc[i])]
                if not len(temp.index == 0):
                    ImpliedVolatilitySurfacePlot_Array[i, j] = 0
                else:
                    ImpliedVolatilitySurfacePlot_Array[i, j] = temp["ImpliedVolatility"].values[0]

        fig = plt.figure(figsize=(15, 12))
        ax = fig.gca(projection='3d')
        surf = ax.plot_surface(OptionDataForPlo_ExercisePrice_Range, OptionDataForPlot_LimitMonth_Range,
                               ImpliedVolatilitySurfacePlot_Array,
                               rstride=2, cstride=2, cmap=plt.cm.coolwarm,
                               linewidth=0.5, antialiased=True)
        ax.set_xlabel('ExercisePrice')
        ax.set_ylabel('limit_month')
        ax.set_zlabel('ImpliedVolatility')
        ax.set_title('ImpliedVolatility Surface at {}'.format(GivenDateTime))
        # ax.set_yticks([0, 1, 2, 3], list(OptionDataForPlot_LimitMonth.values))
        plt.ylim([0, 3])
        plt.xticks(list(range(len(OptionDataForPlo_ExercisePrice_Range))),
                   list(OptionDataForPlot_ExercisePrice.values))
        plt.yticks(list(range(len(OptionDataForPlot_LimitMonth))), list(OptionDataForPlot_LimitMonth.values))

        fig.colorbar(surf, shrink=0.5, aspect=5)

    @staticmethod
    def ImpliedVolatilitySurfacePlot_dropzero(GivenDateTime, Direction="认购"):
        '''
        画给定时刻50ETF隐含波动率曲面，剔除隐含波动率等于0的相关执行价格的合约
        # OptionPlot().ImpliedVolatilitySurfacePlot_dropzero(GivenDateTime)
        :param GivenDateTime:'%Y-%m-%d %H:%M:%S'
        :return:隐含波动率曲面
        '''
        StartDateTime = GivenDateTime
        EndDateTime = dt.datetime.strptime(GivenDateTime, '%Y-%m-%d %H:%M:%S') + dt.timedelta(seconds=1)
        EndDateTime = EndDateTime.strftime('%Y-%m-%d %H:%M:%S')
        OptionRawData = OptionMinuteData.GetDataForListedContractAndUnderlyingSecurity(StartDateTime, EndDateTime)
        OptionRawData = OptionMinuteData.ComputeGreeksForListedContract(OptionRawData)
        OptionDataForPlot = OptionRawData[OptionRawData["call_or_put"] == Direction]
        OptionDataForPlot_LimitMonth = OptionDataForPlot["limit_month"].drop_duplicates().sort_values()

        # 剔除隐含波动率为0的价格
        temp = OptionDataForPlot.groupby("exercise_price")["ImpliedVolatility"].min() > 0.001
        temp = temp.reset_index()
        tempresult = temp[temp["ImpliedVolatility"] == True]
        OptionDataForPlot_ExercisePrice = tempresult["exercise_price"].drop_duplicates().sort_values()
        # 画隐含波动率曲面
        # 画出rsi与pct的相关系数曲面
        OptionDataForPlot_LimitMonth_Range = np.arange(len(OptionDataForPlot_LimitMonth))
        OptionDataForPlo_ExercisePrice_Range = np.arange(len(OptionDataForPlot_ExercisePrice))
        ImpliedVolatilitySurfacePlot_Array = np.empty(
            [len(OptionDataForPlot_ExercisePrice), len(OptionDataForPlot_LimitMonth)])
        OptionDataForPlot_LimitMonth_Range, OptionDataForPlo_ExercisePrice_Range = np.meshgrid(
            OptionDataForPlot_LimitMonth_Range, OptionDataForPlo_ExercisePrice_Range)
        for i in range(len(OptionDataForPlot_ExercisePrice)):
            for j in range(len(OptionDataForPlot_LimitMonth)):
                temp = OptionDataForPlot[
                    (OptionDataForPlot["limit_month"] == OptionDataForPlot_LimitMonth.iloc[j]) & (
                            OptionDataForPlot["exercise_price"] == OptionDataForPlot_ExercisePrice.iloc[i])]
                if not len(temp.index == 0):
                    ImpliedVolatilitySurfacePlot_Array[i, j] = 0
                else:
                    ImpliedVolatilitySurfacePlot_Array[i, j] = temp["ImpliedVolatility"].values[0]

        fig = plt.figure(figsize=(15, 12))
        ax = fig.gca(projection='3d')
        surf = ax.plot_surface(OptionDataForPlo_ExercisePrice_Range, OptionDataForPlot_LimitMonth_Range,
                               ImpliedVolatilitySurfacePlot_Array,
                               rstride=2, cstride=2, cmap=plt.cm.coolwarm,
                               linewidth=0.5, antialiased=True)
        ax.set_xlabel('ExercisePrice')
        ax.set_ylabel('limit_month')
        ax.set_zlabel('ImpliedVolatility')
        ax.set_title('ImpliedVolatility Surface at {}'.format(GivenDateTime))
        # ax.set_yticks([0, 1, 2, 3], list(OptionDataForPlot_LimitMonth.values))
        plt.ylim([0, 3])
        plt.xticks(list(range(len(OptionDataForPlo_ExercisePrice_Range))),
                   list(OptionDataForPlot_ExercisePrice.values))
        plt.yticks(list(range(len(OptionDataForPlot_LimitMonth))), list(OptionDataForPlot_LimitMonth.values))

        fig.colorbar(surf, shrink=0.5, aspect=5)
    @staticmethod
    def ImpliedVolatilitySurfacePlot_dropzero_limitmonth(GivenDateTime, Direction="认购"):
        '''
        画给定时刻50ETF隐含波动率曲面，剔除隐含波动率等于0的相关执行价格的合约以及同一执行价格不够4个的合约。
        :param GivenDateTime:'%Y-%m-%d %H:%M:%S'
        :return:隐含波动率曲面
        '''
        StartDateTime = GivenDateTime
        EndDateTime = dt.datetime.strptime(GivenDateTime, '%Y-%m-%d %H:%M:%S') + dt.timedelta(seconds=1)
        EndDateTime = EndDateTime.strftime('%Y-%m-%d %H:%M:%S')
        OptionRawData = OptionMinuteData.GetDataForListedContractAndUnderlyingSecurity(StartDateTime, EndDateTime)
        OptionRawData = OptionMinuteData.ComputeGreeksForListedContract(OptionRawData)
        OptionDataForPlot = OptionRawData[OptionRawData["call_or_put"] == Direction]
        OptionDataForPlot_LimitMonth = OptionDataForPlot["limit_month"].drop_duplicates().sort_values()

        # 剔除隐含波动率为0的价格
        temp = (OptionDataForPlot.groupby("exercise_price")["ImpliedVolatility"].min() > 0.001) & (
                OptionDataForPlot.groupby("exercise_price")["ImpliedVolatility"].count() == 4)
        temp = temp.reset_index()
        tempresult = temp[temp["ImpliedVolatility"] == True]
        OptionDataForPlot_ExercisePrice = tempresult["exercise_price"].drop_duplicates().sort_values()
        # 画隐含波动率曲面
        # 画出rsi与pct的相关系数曲面
        OptionDataForPlot_LimitMonth_Range = np.arange(len(OptionDataForPlot_LimitMonth))
        OptionDataForPlo_ExercisePrice_Range = np.arange(len(OptionDataForPlot_ExercisePrice))
        ImpliedVolatilitySurfacePlot_Array = np.empty(
            [len(OptionDataForPlot_ExercisePrice), len(OptionDataForPlot_LimitMonth)])
        OptionDataForPlot_LimitMonth_Range, OptionDataForPlo_ExercisePrice_Range = np.meshgrid(
            OptionDataForPlot_LimitMonth_Range, OptionDataForPlo_ExercisePrice_Range)
        for i in range(len(OptionDataForPlot_ExercisePrice)):
            for j in range(len(OptionDataForPlot_LimitMonth)):
                temp = OptionDataForPlot[
                    (OptionDataForPlot["limit_month"] == OptionDataForPlot_LimitMonth.iloc[j]) & (
                            OptionDataForPlot["exercise_price"] == OptionDataForPlot_ExercisePrice.iloc[i])]
                if not len(temp.index == 0):
                    ImpliedVolatilitySurfacePlot_Array[i, j] = 0
                else:
                    ImpliedVolatilitySurfacePlot_Array[i, j] = temp["ImpliedVolatility"].values[0]

        fig = plt.figure(figsize=(15, 12))
        ax = fig.gca(projection='3d')
        surf = ax.plot_surface(OptionDataForPlo_ExercisePrice_Range, OptionDataForPlot_LimitMonth_Range,
                               ImpliedVolatilitySurfacePlot_Array,
                               rstride=2, cstride=2, cmap=plt.cm.coolwarm,
                               linewidth=0.5, antialiased=True)
        ax.set_xlabel('ExercisePrice')
        ax.set_ylabel('limit_month')
        ax.set_zlabel('ImpliedVolatility')
        ax.set_title('ImpliedVolatility Surface at {}'.format(GivenDateTime))
        # ax.set_yticks([0, 1, 2, 3], list(OptionDataForPlot_LimitMonth.values))
        plt.ylim([0, 3])
        plt.xticks(list(range(len(OptionDataForPlo_ExercisePrice_Range))),
                   list(OptionDataForPlot_ExercisePrice.values))
        plt.yticks(list(range(len(OptionDataForPlot_LimitMonth))), list(OptionDataForPlot_LimitMonth.values))

        fig.colorbar(surf, shrink=0.5, aspect=5)

# (OptionDataForPlot.groupby("exercise_price")["ImpliedVolatility"].min()>0.001)
# (OptionDataForPlot.groupby("exercise_price")["ImpliedVolatility"].count()<4)

