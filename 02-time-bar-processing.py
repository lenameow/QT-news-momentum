import pandas as pd
import numpy as np
from datetime import timedelta
from datetime import datetime
from datetime import time
import pytz

def UTCtoEST(timeUTC):
    timezoneEST = pytz.timezone('America/New_York')
    utc = pytz.utc
    timeEST = utc.localize(timeUTC).astimezone(timezoneEST)
    return timeEST

# for base_datetime at exactly 16:00 pm, count as bar 39 of the next trading date
def findNearestDatetime(base_datetime, list_datetime):
    idx = 0
    length_of_list_datetime = len(list_datetime)
    while (idx < length_of_list_datetime) and (list_datetime[idx] <= base_datetime):
        idx = idx + 1
    if idx >= length_of_list_datetime:
        return None
    else:
        return list_datetime[idx]

# for base_datetime at exactly 15-minute bars, count as in the next bar
def findTimeBar(base_datetime):
    start = time(9, 30)
    end = time(16, 0)
    
    if start <= base_datetime.time() < end:
        bar = base_datetime.hour * 4 + int(base_datetime.minute / 15) + 1        
    else:
        bar = 39        
    return bar

if __name__ == '__main__':

    news_data_df = pd.read_csv('rp_equity_filtered_djns2_permno_simplified.csv')
    news_data_df['TIMESTAMP_UTC'] = pd.to_datetime(news_data_df['TIMESTAMP_UTC'])

    # derive date & time bar (to merge with taq_prices.returns_15min table)
    ## read trading dates available
    trading_dates_df = pd.read_csv('trading_dates.csv')
    ## cut off at 4pm on each trading date
    trading_dates_df['date'] = pd.to_datetime(trading_dates_df['date']).apply(\
                            lambda row: (row + timedelta(hours=16)))
    trading_dates_df = trading_dates_df.sort_values(by=['date'])
    trading_dates_ls = trading_dates_df['date'].tolist()


    news_data_df['TIME_EST'] = news_data_df['TIMESTAMP_UTC'].apply(\
            lambda row: UTCtoEST(row).tz_localize(None))
    news_data_taq_period_df = news_data_df[(news_data_df['TIME_EST'] >= datetime(2006, 1, 3, 0, 0, 0)) & \
            (news_data_df['TIME_EST'] <= datetime(2017, 7, 1, 0, 0, 0))]

    news_data_taq_period_df['TIME_EST'] = pd.to_datetime(news_data_taq_period_df['TIME_EST'])
    news_data_taq_period_df = news_data_taq_period_df.sort_values(by=['TIME_EST'])
    news_data_taq_period_df.reset_index(drop=True, inplace=True)

    # find nearest trading date forward for each news timestamp
    news_data_taq_period_df['NEAREST_TRADING_DATE'] = news_data_taq_period_df['TIME_EST'].apply(\
                        lambda row: findNearestDatetime(row, trading_dates_ls))
    # trading_date_datetime to date
    news_data_taq_period_df['date'] = news_data_taq_period_df['NEAREST_TRADING_DATE'].apply(\
                        lambda row: datetime.date(row).strftime('%Y-%m-%d'))
    # derive time bar
    news_data_taq_period_df['bar'] = news_data_taq_period_df['TIME_EST'].apply(\
                        lambda row: findTimeBar(row))

    news_data_taq_period_df.dropna(inplace=True)

    timebars_with_news_df = news_data_taq_period_df[['PERMNO', 'date', 'bar']]
    timebars_with_news_df = timebars_with_news_df.sort_values(by=['PERMNO', 'date', 'bar'])
    timebars_with_news_df.reset_index(drop=True, inplace=True)

    timebars_with_news_df.to_csv('timebars_with_news.csv')