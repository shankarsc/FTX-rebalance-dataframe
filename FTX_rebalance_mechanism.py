import requests
import pandas as pd
import datetime

pd.options.display.float_format = '{:.4f}'.format

response = requests.get('https://ftx.com/api/lt/tokens')
data = pd.DataFrame.from_dict(response.json()['result'])
data.set_index('name', inplace=True)
data['time'] = str(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
bull_bear_tokens = data.filter(regex='BULL|BEAR', axis=0)

rebalance_df = pd.DataFrame()

# Forms the columns for the DataFrame
rebalance_df['time'] = bull_bear_tokens['time']
rebalance_df['underlyingMark'] = bull_bear_tokens['underlyingMark']
rebalance_df['outstanding'] = bull_bear_tokens['outstanding']
rebalance_df['pricePerShare'] = bull_bear_tokens['pricePerShare']
rebalance_df['leverage'] = bull_bear_tokens['leverage']
rebalance_df['currentLeverage'] = bull_bear_tokens['currentLeverage']

# Formula to compute the rebalancing quantity
rebalance_df['desiredPosition'] = bull_bear_tokens['leverage'] * bull_bear_tokens['pricePerShare'] / bull_bear_tokens['underlyingMark']
rebalance_df['currentPosition'] = bull_bear_tokens['currentLeverage'] * bull_bear_tokens['pricePerShare'] / bull_bear_tokens['underlyingMark']
rebalance_df['rebalanceSize'] = (rebalance_df['desiredPosition'] - rebalance_df['currentPosition']) * bull_bear_tokens['outstanding']
rebalance_df['rebalanceSizeDollarNotional'] = rebalance_df['rebalanceSize'] * rebalance_df['underlyingMark']

# Renaming 'BULL' and 'BEAR' tokens to 'BTCBULL' and 'BTCBEAR'
rebalance_df = rebalance_df.reset_index()
mask = (rebalance_df['name']=='BULL') | (rebalance_df['name']=='BEAR') | (rebalance_df['name']=='HALF') | (rebalance_df['name']=='HEDGE')
rebalance_df.loc[mask, 'name'] = "BTC" + rebalance_df.loc[mask, 'name']

# Assigning the underlying names for each BULL/BEAR/BEAR2021 token
rebalance_df['underlying'] = rebalance_df['name'].str.extract(r'(.+?(?=BEAR2021|BEAR|BULL))', expand=False).str.strip().values
rebalance_df['underlying'] =rebalance_df['underlying'] + "-PERP"

# Forming the dataframes to hold each specific BULL, BEAR, and BEAR2021 token
bull_tokens_df = rebalance_df.set_index('name').filter(regex='.+?(?=BULL)', axis=0)
bear_tokens_df = rebalance_df.set_index('name').filter(regex='(.+?(?=(BEAR)\\b))', axis=0)
bear2021_tokens_df = rebalance_df.set_index('name').filter(regex=
                                                           '(.+?(?=(BEAR2021)))', axis=0)

# Computing the rebalance delta for each underlying based on their BULL and BEAR token type
rebalance_delta_df = pd.DataFrame({
    #'time': bull_tokens_df['time'].values,
    'underlying': bull_tokens_df['underlying'].values,
    'underlyingMark': bull_tokens_df['underlyingMark'].values,
    'bullTokenLeverage': bull_tokens_df['currentLeverage'].values,
    'bullTokenRebalSize': bull_tokens_df['rebalanceSizeDollarNotional'].values,
    'bearTokenLeverage': bear_tokens_df['currentLeverage'].values,
    'bearTokenRebalSize': bear_tokens_df['rebalanceSizeDollarNotional'].values,
#    'targetLeverage': bull_tokens_df['leverage'].values,
    'rebalDeltaDollarNotional': (bull_tokens_df['rebalanceSizeDollarNotional'].values - 
                                     bear_tokens_df['rebalanceSizeDollarNotional'].values)
})

# Computing the rebalance delta for MATIC, DOGE, and TOMO based on their BULL and BEAR token type
mask = (rebalance_delta_df['underlying'] == 'DOGE-PERP') | (rebalance_delta_df['underlying'] == 'MATIC-PERP') | (rebalance_delta_df['underlying'] == 'TOMO-PERP')
rebalance_delta_df.loc[mask, 'rebalDeltaDollarNotional'] = rebalance_delta_df[mask]['rebalDeltaDollarNotional'].values + bear2021_tokens_df['rebalanceSizeDollarNotional'].values