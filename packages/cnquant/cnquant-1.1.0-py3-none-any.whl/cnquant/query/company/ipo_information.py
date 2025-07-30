import pandas as pd

from cnquant.config.config_data_path import get_file_path_ipos_information
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)
pd.set_option('display.expand_frame_repr', False)

df = pd.read_csv(get_file_path_ipos_information(), dtype={'SECURITY_CODE': str})
print(df.head(10))
