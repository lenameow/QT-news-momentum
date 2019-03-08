'''
Joining the data using SQL can be extremely slow with only the date as the index.
A possible way I found to cope with the 15 minutes return data, which has more than 200 million rows,
it to use pandas and cut it apart into chunks and then read a part of it, do the join, and then
use concat to combine them up.
'''

import pandas as pd

timebars = pd.read_csv('timebars_with_news-v3-20180624.csv')
del timebars['Unnamed: 0']

timebars['date'] = pd.to_datetime(timebars['date'])

reader = pd.read_csv('returns_15min.csv', iterator=True)
loop = True
chunkSize = 100000
chunks = []
while loop:
    try:
        chunk = reader.get_chunk(chunkSize)
        chunks.append(chunk)
    except StopIteration:
        loop = False
        print ("Iteration is stopped.")

merged_data = []
step = 100
for i in range(0, len(chunks), step):
    if i <= len(chunks) - step:
        bar_data1 = pd.concat(chunks[i:i + step], ignore_index=True)
    else:
        bar_data1 = pd.concat(chunks[i:len(chunks)], ignore_index=True)

    bar_data1.columns = ['PERMNO', 'bar', 'date', 'mid_start', 'mid_end', 'ret']
    bar_data1['date'] = pd.to_datetime(bar_data1['date'])
    merged = pd.merge(timebars, bar_data1, on=['PERMNO', 'date', 'bar'])
    merged_data.append(merged)

merged_data_df = pd.concat(merged_data)
merged_data_df.to_csv('timebars_with_news_merged_with_ret.csv', index=False)