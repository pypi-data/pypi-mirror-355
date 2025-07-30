import pandas as pd

from cnquant.config.config_data_path import (
    get_file_path_holder_num,
)


def holder_num_rank() -> pd.DataFrame:
    df = pd.read_csv(get_file_path_holder_num(), dtype={'symbol': str}, parse_dates=['END_DATE'])

    gb = df.groupby('symbol').apply(lambda x: x.iloc[0])
    gb.sort_values(by='HOLDER_TOTAL_NUM', ascending=False, inplace=True)
    gb.reset_index(drop=True, inplace=True)
    return gb


if __name__ == '__main__':
    a = holder_num_rank()
    print(a.head(50))


