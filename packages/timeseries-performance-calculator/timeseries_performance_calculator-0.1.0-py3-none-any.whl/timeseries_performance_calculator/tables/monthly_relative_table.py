import pandas as pd
from functools import partial
from string_date_controller import MAPPING_MONTHS
from canonical_transformer import map_number_to_signed_string, map_signed_string_to_number
from timeseries_performance_calculator.tables.table_utils import style_table, show_table_performance
from timeseries_performance_calculator.functionals import pipe
from .monthly_returns_table import map_prices_to_table_monthly_returns, style_table_year_monthly

def map_prices_to_table_monthly_relative(prices, ticker_bbg_benchmark=None, option_round=None):
    if ticker_bbg_benchmark is None:
        ticker_bbg_benchmark = prices.columns[1]
    df = map_prices_to_table_monthly_returns(prices).copy()
    index_to_keep = [0, df.index.get_loc(ticker_bbg_benchmark)]
    df = df.iloc[index_to_keep, :]
    if option_round:
        df = df.map(lambda value: map_number_to_signed_string(value=value, decimal_digits=option_round))
        df = df.map(lambda value: map_signed_string_to_number(value=value))
    df.loc['relative', :] = df.T.iloc[:, 0] - df.T.iloc[:, -1]
    return df

def map_table_monthly_relative_to_tables(table_monthly_relative):
    columns = table_monthly_relative.columns
    years = sorted(set([year_month.split('-')[0] for year_month in columns]))
    tables = [table_monthly_relative.loc[:, [year_month for year_month in columns if year_month.split('-')[0] == year]] for year in years]
    return tables

style_table_monthly_relative = style_table_year_monthly

def map_prices_to_tables_monthly_relative(prices, ticker_bbg_benchmark=None, option_round=None, option_signed=False, option_rename_index=False):
    tables = pipe(
        partial(map_prices_to_table_monthly_relative, ticker_bbg_benchmark=ticker_bbg_benchmark, option_round=option_round),
        map_table_monthly_relative_to_tables,
    )(prices)
    return [style_table_monthly_relative(table, option_round=option_round, option_signed=option_signed, option_rename_index=option_rename_index) for table in tables]

get_tables_monthly_relative = map_prices_to_tables_monthly_relative    
show_tables_monthly_relative = partial(map_prices_to_tables_monthly_relative, option_round=4, option_signed=True, option_rename_index=True)

def show_table_monthly_relative_by_year(prices, year=None, option_round=4, option_signed=True, option_rename_index=True):
    tables = map_prices_to_tables_monthly_relative(prices, option_round=option_round, option_signed=option_signed, option_rename_index=option_rename_index)
    years = [table.columns.name for table in tables]
    dct = dict(zip(years, tables))
    if year is None:
        return tables[-1]
    return dct[year]       