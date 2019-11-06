from WindPy import *
import pandas as pd
import numpy as np
from scipy.stats import norm
import datetime as dt

w.start()


class OptionContract:
    '''
    期权合约类
    ContractSet方法:使用wind接口获取上证50ETF全部合约，包括已经摘牌的合约。
    '''

    def __init__(self, exchange="sse", windcode="510050.SH", status="all"):
        self.exchange = exchange
        self.windcode = windcode  # 默认标的为50ETF，将来品种多了后可以调整参数，或者直接实例化
        self.status = status
        self.parameter = "exchange=" + exchange + ";" + "windcode=" + windcode + ";" + "status=" + status

    @classmethod
    def ContractSet(cls):
        '''
        获取期权合约数据集
        :return: 返回期权合约数据集，pandas.dataframe
        '''
        ExchangeLabel = "." + cls().windcode.split(".")[1]  # 判断交易所标签，如"510050.SH"->".SH"
        OptionContractNameRawData = w.wset("optioncontractbasicinfo", cls().parameter)
        OptionContractNameData = pd.DataFrame(OptionContractNameRawData.Data).T
        OptionContractNameData.columns = OptionContractNameRawData.Fields
        OptionContractNameData.index = OptionContractNameData['wind_code'].map(lambda x: str(x) + ExchangeLabel)
        return OptionContractNameData

    @classmethod
    def GetContractInformationByIndex(cls, wind_code):
        '''
        根据wind_code查询期权合约信息
        :param wind_code:
        :return: 返回期权合约信息，pandas.series
        '''
        return cls.ContractSet().loc[wind_code, :]

    @classmethod
    def GetListedContractOnGivenDate(cls, GivenDate):
        '''
        返回指定日期正挂牌交易的合约
        :param GivingDate:给定日期%Y-%m-%d
        :return:返回期权合约数据集，pandas.dataframe
        '''
        return cls.ContractSet()[(cls.ContractSet()["listed_date"] <= dt.datetime.strptime(GivenDate, "%Y-%m-%d")) & (
                cls.ContractSet()["expire_date"] >= dt.datetime.strptime(GivenDate, "%Y-%m-%d"))]

    @classmethod
    def GetListedContractAfterGivenDate(cls, GivenDate):
        '''
        返回指定日期（含）之后曾挂牌交易过的合约，用于数据测算时提取数据使用。包含给定日期后挂牌现在已经摘牌的及仍在交易的。
        :param GivingDate:给定日期%Y-%m-%d
        :return:返回期权合约数据集，pandas.dataframe
        '''
        return cls.ContractSet()[cls.ContractSet()["listed_date"] >= dt.datetime.strptime(GivenDate, "%Y-%m-%d")]

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
        ListedContractInTimeInterval = cls.ContractSet()[
            (cls.ContractSet()["listed_date"] > dt.datetime.strptime(StartDate, "%Y-%m-%d")) & (
                    cls.ContractSet()["listed_date"] <= dt.datetime.strptime(EndDate, "%Y-%m-%d"))]
        return ListedContractOnStartDate.append(ListedContractInTimeInterval)

    @classmethod
    def GetVerticalContractByGivenDate(cls, wind_code, GivenDate):
        '''
        给定期权合约及指定日期，返回其垂直合约列表（不包含本合约）。垂直合约是指同一到期月份不同执行价格的合约。
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
        给定期权合约及指定日期，返回其水平合约列表（不包含本合约）。水平合约是指同执行价格一不同到期月份的合约。
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


# aa=OptionContract.GetVerticalContractByGivenDate("10001504.SH",GivenDate)
# aa1=OptionContract.GetHorizonContractByGivenDate("10001504.SH",GivenDate)

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
        HIGH = 5
        LOW = 0
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
        HIGH = 5
        LOW = 0
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
        HIGH = 5
        LOW = 0
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
        HIGH = 5
        LOW = 0
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


# ToDo 数据接口
class OptionMinuteData(OptionContract, TradeCalendar):
    '''
    分钟级交易数据类，通过wind接口导入分钟级行情数据，并做格式化处理
    1-获取起始日期至终止日期指定合约数据
    2-获取起始日期至终止日期所有曾挂牌交易过的合约数据
    3-获取起始日期至终止日期单一合约及其水平合约数据
    4-获取起始日期至终止日期单一合约及其垂直合约数据
    5-获取起始日期至终止日期单一合约及其T型合约数据
    6-匹配现货标的交易数据
    7-计算希腊字母包括ImpliedVolatility\Delta\Gamma\Vega\Theta\Rho，其余greeks自行添加
    '''

    # OptionContract.ContractSet()[OptionContract.ContractSet()['contract_state'] == "上市"].index
    # OptionContractMinuteData.DateInterVal(365).TradeCalendarData
    @classmethod
    def GetRawData(cls, WindCode, StartDateTime, EndDateTime):
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
