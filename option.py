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

    @classmethod
    def ContractSet(cls):
        '''
        获取期权合约数据集
        :return: 返回期权合约数据集，pandas.dataframe
        '''
        OptionContractNameRawData = w.wset("optioncontractbasicinfo", "exchange=sse;windcode=510050.SH;status=all")
        OptionContractNameData = pd.DataFrame(OptionContractNameRawData.Data).T
        OptionContractNameData.columns = OptionContractNameRawData.Fields
        OptionContractNameData.index = OptionContractNameData['wind_code'].map(lambda x: str(x) + ".SH")
        return OptionContractNameData

    @classmethod
    def GetContractInformationByIndex(cls, wind_code):
        '''
        根据wind_code查询期权合约信息
        :param wind_code:
        :return: 返回期权合约信息，pandas.series
        '''
        return cls.ContractSet().loc[wind_code, :]

    # TODO:明天再写，给定日期后计算当日仍可交易的合约列表
    @classmethod
    def GetListedContractOnGivingDate(cls, GivingDate):
        '''
        返回指定日期挂牌合约
        :param GivingDate:
        :return:
        '''
        pass

    # TODO:明天再写，给定日期后计算当日至今可交易的合约列表
    @classmethod
    def GetListContractAfterGivingDate(cls, GivingDate):
        '''
        返回指定日期（含）之后交易的合约，用于数据测算时提取数据使用
        :param GivingDate:
        :return:
        '''
        pass


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
        定义日历属性
        :return: 返回日历数据，list格式，每一个元素为datetime.date格式
        '''
        return w.tdays(self.StartDate, self.EndDate, "TradingCalendar=SZSE").Times


class OptionContractMinuteData(OptionContract, TradeCalendar):
    '''
    分钟级交易数据类，通过wind接口导入分钟级行情数据，并做格式化处理
    '''

    # OptionContract.ContractSet()[OptionContract.ContractSet()['contract_state'] == "上市"].index
    def __init__(self):
        pass
