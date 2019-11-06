import option
import pandas as pd
TEST = {"Direction": ["认购", "认沽"], "UnderlyingPrice": [3.05, 3.05], "ExercisePrice": [3.00, 3.00],
        "Time": [0.1234, 0.1234], "InterestRate": [0.025, 0.025], "DividendRate": [0, 0], "Volatility": [0.2, 0.2],
        "Close": [0.12, 0.12]}
TEST_df = pd.DataFrame(TEST)




StartDateTime="2019-10-31 08:00:00"
EndDateTime="2019-11-04 20:00:00"
StartDate="2019-10-31"
EndDate="2019-11-04"
WindCode="10002008.SH"

CC=OptionMinuteData.GetRawDataForListedContract(EndDateTime, EndDateTime)



option.ContractSetData
option.OptionContract.GetListedContractOnGivenDate("2019-11-04")

if __name__=="__main__":
    option.OptionGreeksMethod.EuropeanCallPrice(3.05, 3, 0.1234, 0.025, 0, 0.2)
    option.OptionGreeksMethod.EuropeanPutPrice(3.05, 3, 0.1234, 0.025, 0, 0.2)

    TEST_df.apply(option.OptionGreeksMethod.ImpliedVolatilityForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Target="Close")
    TEST_df.apply(option.OptionGreeksMethod.DeltaValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")
    TEST_df.apply(option.OptionGreeksMethod.GammaValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")
    TEST_df.apply(option.OptionGreeksMethod.VegaValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")
    TEST_df.apply(option.OptionGreeksMethod.ThetaValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")
    TEST_df.apply(option.OptionGreeksMethod.RhoValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")
    TEST_df.apply(option.OptionGreeksMethod.VommaValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")
    TEST_df.apply(option.OptionGreeksMethod.VannaValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")
    TEST_df.apply(option.OptionGreeksMethod.CharmValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")
    TEST_df.apply(option.OptionGreeksMethod.VetaValueForApply, axis=1, Direction="Direction",
                  UnderlyingPrice="UnderlyingPrice",
                  ExercisePrice="ExercisePrice", Time="Time",
                  InterestRate="InterestRate",
                  DividendRate="DividendRate",
                  Volatility="Volatility")


