import option
import pandas as pd
TEST = {"Direction": ["认购", "认沽"], "UnderlyingPrice": [3.05, 3.05], "ExercisePrice": [3.00, 3.00],
        "Time": [0.1234, 0.1234], "InterestRate": [0.025, 0.025], "DividendRate": [0, 0], "Volatility": [0.2, 0.2],
        "close": [0.15, 0.15]}
TEST_df = pd.DataFrame(TEST)






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
