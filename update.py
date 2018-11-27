#!/usr/bin/env python3

import requests, json, datetime, time, re
from pprint import pprint
from pymongo import MongoClient

### S1 (=< 11000) Inkjetted holograms /w CASACIUS error
# S1-COIN-1 (Amount == 1)
# S1-COIN-5 (Amount == 5) 
# S1-COIN-25 (Amount == 25) 
# S1-COIN-1000 (Prefix == 1Au) (Amount == 1000)

# S1-BAR-100 (Amount == 100)
# S1-BAR-500 (Amount == 500)
# S1-BAR-1000 (Prefix != 1Au) (Amount == 1000)

### S2 (> 12000, =< 29000) Windowed holograms

# S2-COIN-1 (Amount == 1)
# S2-COIN-5 (Amount == 5) 
# S2-COIN-10 (Amount == 10)
# S2-COIN-25 (Amount == 25)

# S2-BAR-100
# S2-BAR-500

### 2013 Coins (> 29000)

# S2-COIN-BRASS-HALF = 0.5 Brass (Prefix == 12) (Value = 0.5)
# S2-COIN-BRASS-ONE = 1.0 Brass (Prefix = 13) (Value == 1)
# S2-COIN-AG-TENTH = 0.1 Fine Silver BTC (Prefix == 1Ag) (Value == 0.1)
# S2-COIN-AG-HALF = 0.5 Fine Silver BTC (Prefix == 1Ag) (Value == 0.5)
# S2-COIN-AG-ONE = 1.0 Fine Silver BTC (Prefix == 1Ag) (Value == 1)

### S3
# S3-COIN-ONE
# S3-COIN-HALF

# Coin Status (coin_status):
# 1. Nonexistent
# 2. Active
# 3. Redeemed

client = MongoClient('localhost', 27017)
db = client.tracker
casascius_list = db.coin.find( 
  { "$and" :
    [
      { "$or":
        [
          {'status': 'Active'},
          {'status': 'Redeemed'},
          #{'status': 'Unused'}
        ]
      },
      { 'index' :
        { '$gt': 0 }
      },
    ] 
  },
  no_cursor_timeout=True
)

update_time = int(time.time())

for coin in casascius_list:
  coin_index = coin['index']
  coin_address = coin['address']
  pagination = 25
  coin_result = requests.get('https://api.smartbit.com.au/v1/blockchain/address/%s?limit=%s&sort=txindex&dir=asc' % (coin_address, pagination)).json()['address']

  coin_type = None	
  coin_series = None
  coin_status = 'Unused'
  addr_balance = float(coin_result['total']['balance'])
  addr_tx_count = coin_result['total']['transaction_count']
  addr_in_count = coin_result['total']['input_count']
  addr_out_count = coin_result['total']['output_count']

  fund_value = None
  fund_tx_id = None
  fund_tx_time = None
  fund_tx_block = None
  
  spend_tx_id = None
  spend_tx_time = None
  spend_tx_block = None

  # If funded
  if addr_tx_count != 0:
    coin_status = 'Active'

    # Build tx list, Loop if multiple pages of transactions and append to transaction list	
    addr_transactions = coin_result['transactions']
    transactions_next_page = coin_result['transaction_paging']['next_link']
    while transactions_next_page is not None:
      tx_next_page = requests.get(transactions_next_page).json()['address']
      addr_transactions.extend(tx_next_page['transactions'])
      transactions_next_page = tx_next_page['transaction_paging']['next_link']

    fund_tx = addr_transactions[0]
    fund_tx_id = fund_tx['txid']
    fund_tx_output = list(filter(lambda f : f['addresses'][0] == coin_address, fund_tx['outputs']))[0]
    fund_value = float(fund_tx_output['value'])
    fund_tx_block = fund_tx['block']
    fund_tx_time = fund_tx['time']

    if float(fund_value) == 1.0:
      if coin_index <= 11000:
        coin_series = "1"
        coin_type = "S1-COIN-1"
      elif coin_index > 11000:
        if re.match(r'^1Ag', coin_address):
          coin_series = "3"
          coin_type = "S3-COIN-1-AG"
        else:
          if fund_tx_time >= 1293840000 and fund_tx_time < 1325376000:
            coin_series = "2"
            coin_type = "S2-COIN-1-2011"
          elif fund_tx_time >= 1325376000 and fund_tx_time < 1356998400:
            coin_series = "2"
            coin_type = "S2-COIN-1-2012"
          elif fund_tx_time >= 1356998400:
            coin_series = "2"
            coin_type = "S2-COIN-1-2013"
    
    elif float(fund_value) == 0.5:
      if re.match(r'^1Ag', coin_address):
        coin_series = "3"
        coin_type = "S3-COIN-0.5-AG"
      else:
        coin_series = "2"
        coin_type = "S2-COIN-0.5"
    
    elif float(fund_value) == 0.1:
      coin_series = "3"
      coin_type = "S3-COIN-0.1-AG"
    
    elif float(fund_value) == 5.0:
      if coin_index <= 11000:
        coin_series = "1"
        coin_type = "S1-COIN-5"
      elif coin_index > 11000:
        coin_series = "2"
        coin_type = "S2-COIN-5"
    
    elif float(fund_value) == 10.0:
      coin_series = "2"
      coin_type = "S2-COIN-10"

    elif float(fund_value) == 25.0:
      if coin_index <= 11000:
        coin_series = "1"
        coin_type = "S1-COIN-25"
      elif coin_index > 11000:
        coin_series = "2"
        coin_type = "S2-COIN-25"
    
    elif float(fund_value) == 100.0:
      if coin_index <= 11000:
        coin_series = "1"
        coin_type = "S1-BAR-100"
      elif coin_index > 11000:
        coin_series = "2"
        coin_type = "S2-BAR-100"

    elif float(fund_value) == 500.0:
      if coin_index <= 11000:
        coin_series = "1"
        coin_type = "S1-BAR-500"
      elif coin_index > 11000:
        coin_series = "2"
        coin_type = "S2-BAR-500"

    elif float(fund_value) == 1000.0:
      if re.match(r'^1Au', coin_address):
        coin_series = "1"
        coin_type = "S1-COIN-1000"
      else:
        coin_series = "1"
        coin_type = "S1-BAR-1000"
    
    elif float(fund_value) > 0:
      coin_series = "2"
      coin_type = "S2-BAR-DIY"

    # If Spent
    if addr_out_count != 0:
      coin_status = 'Redeemed'
	
      for tx in addr_transactions:
				
        # Only check non-coinbse transactions
        if tx['coinbase'] is False:
          spend_tx_id = tx['txid']
          spend_tx = list(filter(lambda f : f['addresses'][0] == coin_address, tx['inputs']))

          if len(spend_tx) > 0:
            spend_tx_input = spend_tx[0]
            spend_tx_block = tx['block']
            spend_tx_time = tx['time']
            break

  #db.Coin.insert_one({
  mongo_document= { 
    'index': coin_index,
    'address': coin_address,
    'balance': addr_balance,
    'txcount': addr_tx_count,
    'incount': addr_in_count,
    'outcount': addr_out_count,
    'create_txid': fund_tx_id,
    'create_block': fund_tx_block,
    'create_time': fund_tx_time,
    'redeem_txid': spend_tx_id,
    'redeem_block': spend_tx_block,
    'redeem_time': spend_tx_time,
    'value': fund_value,
    'type': coin_type,
    'status': coin_status,
    'series': coin_series,
    'update_time': update_time,
  }

  db.coin.update_one({'address': coin_address}, {'$set': mongo_document}, upsert=True)

  # Print Outputs
  print(('%-20s: %s') % ('Index', coin_index))
  print(('%-20s: %s') % ('Address', coin_address))
  print(('%-20s: %s') % ('Balance', addr_balance))
  print(('%-20s: %s') % ('Tx Count', addr_tx_count))
  print(('%-20s: %s') % ('In Count', addr_in_count))
  print(('%-20s: %s') % ('Out Count', addr_out_count))
  print('')
  print(('%-20s: %s') % ('Fund Txid', fund_tx_id))
  print(('%-20s: %s') % ('Fund Block', fund_tx_block))
  print(('%-20s: %s') % ('Fund Time', fund_tx_time))
  print('')
  print(('%-20s: %s') % ('Spend Txid', spend_tx_id))
  print(('%-20s: %s') % ('Spend Block', spend_tx_block))
  print(('%-20s: %s') % ('Spend Time', spend_tx_time))
  print('')
  print(('%-20s: %s') % ('Coin Value', fund_value))
  print(('%-20s: %s') % ('Coin Type', coin_type))
  print(('%-20s: %s') % ('Coin Series', coin_series))
  print(('%-20s: %s') % ('Coin Status', coin_status))
  print('-----------------------------------------------------------------------------------------------')
