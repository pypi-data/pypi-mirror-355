import pandas as pd
from typing import Tuple
from universal_timeseries_transformer import PricesMatrix
from .monthly_cumreturns_table import get_monthly_cumreturns_table, add_alpha_column, get_prices_with_benchmark

def map_prices_to_relative(prices: pd.DataFrame, benchmark_column: str) -> pd.DataFrame:
    df = get_monthly_cumreturns_table(prices).copy()
    columns = df.columns
    idx = columns.get_loc(benchmark_column)
    # for col in columns:
    #     df[col] = df[col] - df.iloc[:, idx]
    # not working because of broadcasting
    benchmark_values = df.iloc[:, idx].values.reshape(-1, 1)
    df_result = df.sub(benchmark_values, axis=0)
    return df_result

def add_wins_row_to_relative(df_relative: pd.DataFrame) -> pd.DataFrame:
    df = df_relative.copy()
    wins = df.apply(lambda col: int((col > 0).sum()))
    df.loc['wins', :] = wins
    return df

def get_row_wins(df_relative: pd.DataFrame) -> pd.DataFrame:
    df = add_wins_row_to_relative(df_relative)
    return df.iloc[[-1], :]

def add_winning_ratio_row_to_relative(df_relative: pd.DataFrame) -> pd.DataFrame:
    df = df_relative.copy()
    winning_ratio = df.apply(lambda col: (col > 0).mean())
    df.loc['winning_ratio', :] = winning_ratio
    return df

def get_row_winning_ratio(df_relative: pd.DataFrame) -> pd.DataFrame:
    df = add_winning_ratio_row_to_relative(df_relative)
    return df.iloc[[-1], :]

def map_relative_to_winning(df_relative: pd.DataFrame) -> pd.DataFrame:
    row_wins = get_row_wins(df_relative)
    row_winning_ratio = get_row_winning_ratio(df_relative)
    df = pd.concat([df_relative, row_wins, row_winning_ratio], axis=0)
    return df

def get_df_winning_ratio(prices: pd.DataFrame, benchmark_column: str) -> pd.DataFrame:
    df_relative = map_prices_to_relative(prices, benchmark_column)
    df = map_relative_to_winning(df_relative)
    return df

def get_data_df_winning_ratio_by_year(prices: pd.DataFrame, benchmark_column: str) -> pd.DataFrame:
    df = map_prices_to_relative(prices, benchmark_column)
    df['year'] = df.index.str.split('-').str[0]
    dct_dfs = dict(tuple(df.groupby('year')))
    return {year: map_relative_to_winning(df.drop('year', axis=1)) for year, df in dct_dfs.items()}
    
def get_df_winning_ratio_by_year(prices: pd.DataFrame, benchmark_column: str, year: str) -> pd.DataFrame:
    dct_dfs = get_data_df_winning_ratio_by_year(prices, benchmark_column)
    return dct_dfs[year]

def show_yearly_winning_ratio_table(prices: pd.DataFrame, benchmark_column: str, option_dash: bool = False) -> pd.DataFrame:
    dct_dfs = get_data_df_winning_ratio_by_year(prices, benchmark_column)
    dfs = []
    for year, df in dct_dfs.items():
        df = df.iloc[-1:, :].copy()
        df.index = [year]
        df[benchmark_column] = '-' if option_dash else df[benchmark_column]
        dfs.append(df)
    df = pd.concat(dfs, axis=0)
    df.index.name = 'winning_ratio'
    return df

def show_winning_ratio_table(prices: pd.DataFrame, benchmark_column: str, option_dash: bool = False) -> pd.DataFrame:
    df = get_df_winning_ratio(prices, benchmark_column).copy()
    df[benchmark_column] = '-' if option_dash else df[benchmark_column]
    df.index.name = None
    return df.iloc[-2:, :]

def map_relative_to_det(df_relative: pd.DataFrame) -> pd.DataFrame:
    determinator = lambda x: True if x > 0 else False if x < 0 else None
    df = df_relative.copy()
    df = df.map(determinator)
    return df

def map_det_to_wins(df_det: pd.DataFrame) -> pd.DataFrame:
    df = df_det.copy()
    wins = df.apply(lambda col: col.value_counts().get(True, 0))
    df.loc['wins', :] = wins
    return df


# def calculate_wins_and_loses(prices: pd.DataFrame, benchmark_column: str) -> Tuple[int, int]:
#     df_winning = get_winning_table(prices, benchmark_column)
#     wins = (df_winning['win']==True).sum()
#     loses = (df_winning['win']==False).sum()
#     return wins, loses

# def calculate_winning_ratios(prices: pd.DataFrame, benchmark_column: str) -> Tuple[float, float]:
#     wins, loses = calculate_wins_and_loses(prices, benchmark_column)
#     return wins / (wins + loses), loses / (wins + loses)

# def show_winning_ratio_table(prices: pd.DataFrame, benchmark_column: str) -> pd.DataFrame:
#     wins, loses = calculate_wins_and_loses(prices, benchmark_column)
#     winning_ratio, losing_ratio = calculate_winning_ratios(prices, benchmark_column)
#     columns = prices.columns
#     df = pd.DataFrame(
#         index = ,
#     )
    