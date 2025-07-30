import pandas as pd
from functools import partial
from string_date_controller import MAPPING_MONTHS
from universal_timeseries_transformer import PricesMatrix
from canonical_transformer import map_number_to_signed_string, map_signed_string_to_number
from timeseries_performance_calculator.tables.table_utils import style_table, show_table_performance
from timeseries_performance_calculator.basis.return_calculator import calculate_return
from timeseries_performance_calculator.functionals import pipe


def map_prices_to_table_monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    pm = PricesMatrix(prices)

    def create_table(year_month, date_pair):
        columns = pm.rows_by_names((date_pair[0], date_pair[1])).T
        returns = calculate_return(columns.iloc[:, 0], columns.iloc[:, -1])
        return returns.to_frame(year_month)
    
    tables = [create_table(year_month, date_pair) 
              for year_month, date_pair in pm.monthly_date_pairs.items()]
    return pd.concat(tables, axis=1)

get_table_monthly_returns = map_prices_to_table_monthly_returns
show_table_monthly_returns = partial(show_table_performance, get_table_monthly_returns)

def map_prices_to_table_monthly_relative(prices, ticker_bbg_benchmark, option_round=None):
    df = map_prices_to_table_monthly_returns(prices).copy()
    index_to_keep = [0, df.index.get_loc(ticker_bbg_benchmark)]
    df = df.iloc[index_to_keep, :]
    if option_round:
        df = df.map(lambda value: map_number_to_signed_string(value=value, decimal_digits=option_round))
        df = df.map(lambda value: map_signed_string_to_number(value=value))
    df.loc['relative', :] = df.T.iloc[:, 0] - df.T.iloc[:, -1]
    return df

def map_table_monthly_to_tables(table):
    columns = table.columns
    years = sorted(set([year_month.split('-')[0] for year_month in columns]))
    tables = [table.loc[:, [year_month for year_month in columns if year_month.split('-')[0] == year]] for year in years]
    return tables

def style_table_year_monthly(table, option_round=4, option_signed=True, option_rename_index=True):
    table = table.copy()
    table = style_table(table, option_round=option_round, option_signed=option_signed, option_rename_index=option_rename_index)
    year = table.columns[0].split('-')[0]
    table.columns = [MAPPING_MONTHS[year_month.split('-')[1]] for year_month in table.columns]
    table.columns.name = year
    table = table.T.reindex(MAPPING_MONTHS.values()).T.fillna('-')
    return table
