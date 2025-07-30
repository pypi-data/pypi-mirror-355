from typing import Callable

import pandas as pd
from tqdm.auto import tqdm


def concat_dfs(func: Callable, datas: list):
    dfs = []
    # 获取数据
    for data in tqdm(datas):
        df = func(data)
        dfs.append(df)
    # 合并数据
    data_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)
    return data_df

