import pandas as pd
from functools import partial
from timeseries_performance_calculator.tables import (
    get_table_annualized_return_cagr,
    get_table_annualized_return_days,
    get_table_annualized_volatility,
    get_table_maxdrawdown,
)
from timeseries_performance_calculator.tables.table_utils import show_table_performance

def map_prices_to_table_total_performance(prices: pd.DataFrame)-> pd.DataFrame:
    table_cagr = get_table_annualized_return_cagr(prices)
    table_days = get_table_annualized_return_days(prices)
    table_av = get_table_annualized_volatility(prices)
    table_mdd = get_table_maxdrawdown(prices)
    return pd.concat([table_cagr, table_days, table_av, table_mdd], axis=1)

get_table_total_performance = map_prices_to_table_total_performance
show_table_total_performance = partial(show_table_performance, map_prices_to_table_total_performance)
