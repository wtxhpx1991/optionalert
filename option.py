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
