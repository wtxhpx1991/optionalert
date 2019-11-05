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
    获取交易日历
    '''

    def __init__(self, StartDate, EndDate):
        '''
        使用wind接口获取交易日历
        :param StartDate: 起始日期%Y-%m-%d
        :param EndDate: 终止日期%Y-%m-%d
        '''
        self.StartDate = StartDate
        self.EndDate = EndDate

    # w.tdays("2018-01-01", "2020-12-31", "TradingCalendar=SZSE").Times
    # dt.datetime.today().date().strftime('%Y-%m-%d')
    @staticmethod
    def DateInterVal(DateInterval=365):
        '''
        静态方法，初始化实例可返回以当前日向前后一段时间的实例
        :param DateInterval:日期，int格式
        :return:
        '''
        StartDate = dt.datetime.today().date() + dt.timedelta(days=-DateInterval)
        EndDate = dt.datetime.today().date() + dt.timedelta(days=DateInterval)
        StartDate = StartDate.strftime('%Y-%m-%d')
        EndDate = EndDate.strftime('%Y-%m-%d')
        return TradeCalendar(StartDate, EndDate)

    @property
    def TradeCalendarData(self):
        '''
        定义属性，返回日历数据
        :return: 返回日历数据，list格式，每一个元素为datetime.date格式
        '''
        return w.tdays(self.StartDate, self.EndDate, "TradingCalendar=SZSE").Times


# TODO 计算期权希腊字母
class OptionGreeksMethod:
    '''
    计算给定欧式期权合约数据，计算期权的希腊字母，包括以下几个类方法：
    1-看涨期权价格计算EuropeanCallPrice
    2-看跌期权价格计算EuropeanPutPrice
    3.1-看涨期权隐含波动率计算ImpliedCallVolatility
    3.2-看涨期权隐含波动率计算ImpliedCallVolatilityForApply
    4.1-看跌期权隐含波动率计算ImpliedPutVolatility
    4.2-看跌期权隐含波动率计算ImpliedPutVolatilityForApply
    5-期权隐含波动率计算（基于call_or_put字段）ImpliedVolatility
    6-DELTA计算DeltaValue
    6.1-看涨期权CallDeltaValue
    6.2-看涨期权CallDeltaValueForApply
    6.3-看跌期权PutDeltaValue
    6.4-看跌期权PutDeltaValueForApply
    7-GAMMA计算GammaValue
    7.1-GammaValue
    7.2-GammaValueForApply
    8-VEGA计算VegaValue
    9-THETA计算ThetaValue
    10-RHO计算RhoValue
    其中，3.2、4.2、5、6、7、8、9、10增加了ArrLike参数，用于对pandas.dataframe格式数据使用apply方法
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
    def ImpliedVolatility(cls, ArrLike, Direction, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate,
                          Target):
        '''
        5-期权隐含波动率计算（基于call_or_put字段）ImpliedVolatility
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

    # TODO 计算希腊字母
    @classmethod
    def DeltaValue(cls, UnderlyingPrice, ExercisePrice, Time, InterestRate, DividendRate, Volatility):
        '''
        6-DELTA计算DeltaValue
        :param UnderlyingPrice:
        :param ExercisePrice:
        :param Time:
        :param InterestRate:
        :param DividendRate:
        :param Volatility:
        :return:
        '''
        pass


class OptionContractMinuteData(OptionContract, TradeCalendar):
    '''
    分钟级交易数据类，通过wind接口导入分钟级行情数据，并做格式化处理
    '''

    # OptionContract.ContractSet()[OptionContract.ContractSet()['contract_state'] == "上市"].index
    def __init__(self):
        pass
