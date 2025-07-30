import pandas as pd

from cnquant.config.config_data_path import get_file_path_dividend_ths

df = pd.read_csv(get_file_path_dividend_ths())
print(df.head(100))
