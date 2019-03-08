import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

crsp = pd.read_pickle('crsp_dsf_filtered.pickle')
# If you'll run this program for many times, it's recommended to convert the csv file to pickle for faster speed.
# crsp = pd.read_csv('crsp_dsf_filtered.csv')
news_ret = pd.read_csv('timebars_with_news_merged_with_ret.csv')
trading_dates = pd.read_csv('trading_dates.csv')
crsp.drop_duplicates(inplace=True)
news_ret.drop_duplicates(inplace=True)

news_ret['date'] = pd.to_datetime(news_ret['date'])
crsp['date'] = pd.to_datetime(crsp['date'])
trading_dates['date'] = pd.to_datetime(trading_dates['date'])

news_ret.rename(columns={'ret': 'ret_news', 'PERMNO' : 'permno'}, inplace=True)
news_ret.sort_values(['date', 'permno', 'bar'], inplace = True)

# Add columns of the data in the next 5 days (t+1 to t+5)
crsp['ret_t1'] = crsp.groupby('permno')['ret'].shift(-1)
crsp['ret_t2'] = crsp.groupby('permno')['ret'].shift(-2)
crsp['ret_t3'] = crsp.groupby('permno')['ret'].shift(-3)
crsp['ret_t4'] = crsp.groupby('permno')['ret'].shift(-4)
crsp['ret_t5'] = crsp.groupby('permno')['ret'].shift(-5)

crsp['shrout_t1'] = crsp.groupby('permno')['shrout'].shift(-1)
crsp['shrout_t2'] = crsp.groupby('permno')['shrout'].shift(-2)
crsp['shrout_t3'] = crsp.groupby('permno')['shrout'].shift(-3)
crsp['shrout_t4'] = crsp.groupby('permno')['shrout'].shift(-4)
crsp['shrout_t5'] = crsp.groupby('permno')['shrout'].shift(-5)

news_ret_merged = pd.merge(news_ret, crsp, on=['permno', 'date'])
news_ret_merged.dropna(inplace=True)

# Calculate mcap and filter out those mcap < 100000
news_ret_merged['mcap'] = news_ret_merged['prc'] * news_ret_merged['shrout']
news_ret_merged = news_ret_merged[np.log10(news_ret_merged['mcap']) >= 5]

# Apply quantile
news_ret_merged['ret_news_bins'] = news_ret_merged.groupby('date')['ret_news'].\
    apply(lambda x: pd.Series(pd.qcut(x.rank(method='first'), 10, list(range(1,11))), index=x.index))

# Make sure that the shares out is not changed, otherwise deleted (this probably will cause look-ahead bias)
# news_ret_merged = news_ret_merged[(news_ret_merged['shrout'] == news_ret_merged['shrout_t1']) & (news_ret_merged['shrout_t1'] == news_ret_merged['shrout_t2']) & (news_ret_merged['shrout_t2'] == news_ret_merged['shrout_t3']) & (news_ret_merged['shrout_t3'] == news_ret_merged['shrout_t4'])  & (news_ret_merged['shrout_t4'] == news_ret_merged['shrout_t5'])]

# Filter out those day t return > 100% or < -50% (considered them abnormal)
news_ret_merged = news_ret_merged[(news_ret_merged['ret'] <= 1) & (news_ret_merged['ret'] >= -0.5)]

strategy_long = news_ret_merged[news_ret_merged['ret_news_bins'] == 10]
strategy_short = news_ret_merged[news_ret_merged['ret_news_bins'] == 1]

# Function for calculating the unrealized returns
def ret_unrealized(df):
    ret_unre = []
    ret_unre.append(df['ret_t1'][0])
    ret_unre.append((1+df['ret_t1'][1]) * (1+df['ret_t2'][0]) - 1)
    ret_unre.append((1+df['ret_t1'][2]) * (1+df['ret_t2'][1]) * (1+df['ret_t3'][0]) - 1)
    ret_unre.append((1+df['ret_t1'][3]) * (1+df['ret_t2'][2]) * (1+df['ret_t3'][1]) * (1+df['ret_t4'][0]) - 1)
    for i in range(4, len(df)):
        ret_unre.append((1+df['ret_t1'][i]) * (1+df['ret_t2'][i-1]) * (1+df['ret_t3'][i-2]) * (1+df['ret_t4'][i-3]) * (1+df['ret_t5'][i-4]) - 1)
    return ret_unre

# These functions are similar to those used in assignments
def weighted_average(df, x, weight):
    return (df[x] * df[weight]).sum() / df[weight].sum()

# This one is weighted by mcap, hasn't be updated for the unrealized return
# def strategy_return(strategy_long, strategy_short):
#     # Constructing strategy
#     portfolio_long = strategy_long[['ret_5days', 'date', 'mcap']]
#     portfolio_long = pd.DataFrame(portfolio_long.groupby('date').apply(weighted_average, 'ret_5days', 'mcap'), columns=['return'])
#     portfolio_short = strategy_short[['ret_5days', 'date', 'mcap']]
#     portfolio_short = pd.DataFrame(portfolio_short.groupby('date').apply(weighted_average, 'ret_5days', 'mcap'), columns=['return'])
#
#     ret_merge = pd.merge(portfolio_long, portfolio_short, on='date', suffixes=['_long', '_short'])
#     ret_merge['return'] = ret_merge['return_long'] - ret_merge['return_short']
#     return ret_merge

# This one is equal weighted
def strategy_return_equal_weight(strategy_long, strategy_short):
    # Constructing strategy
    portfolio_long = strategy_long[['ret_t1', 'ret_t2', 'ret_t3', 'ret_t4', 'ret_t5', 'date']]
    portfolio_long = pd.DataFrame(portfolio_long.groupby('date').mean())
    portfolio_short = strategy_short[['ret_t1', 'ret_t2', 'ret_t3', 'ret_t4', 'ret_t5', 'date']]
    portfolio_short = pd.DataFrame(portfolio_short.groupby('date').mean())

    ret_merge = pd.merge(portfolio_long, portfolio_short, left_index=True, right_index=True, suffixes=['_long', '_short'])

    ret_merge['ret_t1'] = ret_merge['ret_t1_long'] - ret_merge['ret_t1_short']
    ret_merge['ret_t2'] = ret_merge['ret_t2_long'] - ret_merge['ret_t2_short']
    ret_merge['ret_t3'] = ret_merge['ret_t3_long'] - ret_merge['ret_t3_short']
    ret_merge['ret_t4'] = ret_merge['ret_t4_long'] - ret_merge['ret_t4_short']
    ret_merge['ret_t5'] = ret_merge['ret_t5_long'] - ret_merge['ret_t5_short']

    ret_merge['return'] = ret_unrealized(ret_merge)
    ret_merge['return'][ret_merge['return'] <= -1] = 0
    return ret_merge

ret_merge = strategy_return_equal_weight(strategy_long, strategy_short)
ret_merge['cumulative_return'] = np.cumprod(1+ret_merge['return']) - 1

# Shift the date of returns
start_date_index = int(trading_dates.index[trading_dates['date'] == ret_merge.index[0]][0]) + 1
end_date_index = int(trading_dates.index[trading_dates['date'] == ret_merge.index[-1]][0]) + 1
ret_merge.index = trading_dates.iloc[start_date_index:end_date_index + 1]['date'].values

# ret_merge.to_csv('ret_merge.csv')

# Plot
fig = plt.figure(1, (16, 9))
ax = fig.add_subplot(1, 1, 1)
x = pd.to_datetime(ret_merge.index)
y = ret_merge['cumulative_return']+1
plt.plot(x, y)
plt.ylabel("Portfolio Value")
plt.xlabel('date')

# y axis scale is set to log
ax = plt.gca()
ax.set_yscale('log')
plt.tick_params(axis='y', which='minor')
ax.yaxis.set_minor_formatter(FormatStrFormatter("%.1f"))

plt.show()

# Calculate Sharpe ratio
def sharpe_ratio(returns, annual_factor):
    print('mean', np.mean(returns), 'volatility', np.std(returns))
    sharpe_ratio = np.mean(returns) / np.std(returns)
    print('sharpe_ratio', sharpe_ratio)
    print('sharpe_ratio annualized', sharpe_ratio * np.sqrt(annual_factor))
    print()

sharpe_ratio(ret_merge['return'], 250)