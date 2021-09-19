import requests
import pandas as pd
import datetime
import numpy as np

pd.options.display.float_format = '{:.4f}'.format

# Query rebalance info for leveraged tokens from FTX
response = requests.get('https://ftx.com/api/etfs/rebalance_info')

# Pass `response` into a DataFrame
df = pd.DataFrame(eval(response.json()['result'])).T.reset_index()
df = df.sort_values('time', ascending=False)

# regex to drop indexes which do not have an underlying perpetual to rebalance off of
# ['BVOL', 'IBVOL', 'BTMXBEAR', 'BTMXBULL', 'BTMXHEDGE', 'BTMXHALF']
mask = (df['index']=='BVOL') | (df['index']=='IBVOL') | (df['index']=='BTMXBEAR') | (df['index']=='BTMXBULL') | (df['index']=='BTMXHEDGE') | (df['index']=='BTMXHALF')
df.drop(df[mask].index.values, inplace=True)

# More transformations, querying underlying name from token name and appending '-PERP'
df['underlying'] = df['index'].str.extract(r'(.+?(?=BEAR2021|BEAR|BULL|HALF|HEDGE))', expand=False).str.strip().values
df['underlying'].fillna(df['index'], inplace=True)
df['underlying'] = df['underlying'] + '-PERP'

# Specifying the underlying (BTC-PERP) for 'BULL', 'BEAR', 'HALF', and 'HEDGE' tokens
mask = (df['index']=='BULL') | (df['index']=='BEAR') | (df['index']=='HALF') | (df['index']=='HEDGE')
df.loc[mask, 'underlying'] = "BTC-PERP"
df.loc[mask, 'index'] = "BTC" + df.loc[mask, 'index']

# Specifying the underlying (SHIT-PERP) for 'BULLSHIT', 'BEARSHIT', 'HALFSHIT', and 'HEDGESHIT' tokens
mask = (df['index']=='BULLSHIT') | (df['index']=='BEARSHIT') | (df['index']=='HALFSHIT') | (df['index']=='HEDGESHIT')
df.loc[mask, 'underlying'] = "SHIT-PERP"

# Formatting the 'time' column when rebalance occured. Obtain the 'start_time' and 'end_time' ('start_time' + 60s) to when rebalance occurred.
df['time'] = pd.to_datetime(df['time'])
df['rounded_time'] = df['time'].round('min')
df['start_time'] = df['rounded_time'].astype(np.int64) // 10**9
df['end_time'] = df['start_time'] + 60
df = df.reset_index().drop('level_0', axis=1)

# Initialising the DataFrames
temp_df = pd.DataFrame()
temp_df1 = pd.DataFrame()

# Obtain the kline data for each index for the specific rebalance period
for row in range(len(df)):
    response = requests.get('https://ftx.com/api/markets/{}/candles?resolution=60&start_time={}&endtime={}'
                            .format(df['underlying'][row], 
                                    df['start_time'][row], 
                                    df['end_time'][row])) 
    
    temp_df1 = pd.DataFrame.from_dict(response.json()['result'])
    temp_df = temp_df.append(temp_df1.iloc[0])

# Further transformations
temp_df['underlying'] = df['underlying'].values
temp_df = temp_df[['underlying', 'startTime', 'open', 'high', 'low', 'close', 'volume']]
temp_df = temp_df.reset_index(drop=True)

transformed_df = df.merge(temp_df, how='inner', on=temp_df.index)
transformed_df = transformed_df[['time', 'index', 'orderSizeList', 'side', 'underlying_x', 'open', 'high', 'low', 'close', 'volume']]
