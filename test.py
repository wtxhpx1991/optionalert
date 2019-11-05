import option
import pandas as pd










TEST = {"Direction": ["认购", "认沽"], "UnderlyingPrice": [3.05, 2.95], "ExercisePrice": [3.00, 3.00],
        "Time": [0.1234, 0.1234], "InterestRate": [0.025, 0.025], "DividendRate": [0, 0], "Volatility": [0.2, 0.2],
        "close": [0.15, 0.13]}
TEST_df = pd.DataFrame(TEST)
TEST_df.apply(option.OptionGreeksMethod.ThetaValueForApply, axis=1, Direction="Direction",
              UnderlyingPrice="UnderlyingPrice",
              ExercisePrice="ExercisePrice", Time="Time",
              InterestRate="InterestRate",
              DividendRate="DividendRate",
              Volatility="Volatility")


