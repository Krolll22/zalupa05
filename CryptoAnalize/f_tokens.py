import time
import time
from datetime import datetime

import requests

from f_const import ETHERSCAN_API_KEY, UNISWAP_V3_URL, UNISWAP_V2_URL, WETH_ADDRESS, TOTAL_VALUE_LOCKED_ETH_MIN, \
    WETH_USDC_PAIR_V3, USDC_ADDRESS, STABLE_COINS_ARR, CRYPTO_ARRAY, WETH_USDC_PAIR_V2
from f_http_request import requestGet


# NEW
def get_valid_pool_v2v3(token_address, isLockedEth, isCycleNeeded = False, timestamp=None):
    if isLockedEth:
        pool_v3 = get_valid_pool_for_token_v3(token_address, TOTAL_VALUE_LOCKED_ETH_MIN, 5, isCycleNeeded, timestamp)
    else:
        pool_v3 = get_valid_pool_for_token_v3(token_address, 0, 0, isCycleNeeded, timestamp)

    if pool_v3:
        print("v3")
        print(pool_v3)
        return {
            'version': pool_v3['version'],
            'id': pool_v3['id'],
            'token0': pool_v3['token0'],
            'token1': pool_v3['token1'],
            'compareTokenId': pool_v3['compareTokenId']
        }
    else:
        if isLockedEth:
            pool_v2 = get_valid_pair_for_token_v2(token_address, TOTAL_VALUE_LOCKED_ETH_MIN,isCycleNeeded,timestamp)
        else:
            pool_v2 = get_valid_pair_for_token_v2(token_address, 0, isCycleNeeded, timestamp)
        if pool_v2:
            print("v2")
            print(pool_v2)
            return {
                'version': pool_v2['version'],
                'id': pool_v2['id'],
                'token0': pool_v2['token0'],
                'token1': pool_v2['token1'],
                'compareTokenId': pool_v2['compareTokenId']
            }
    return None


# NEW
def get_valid_pool_for_token_v3(token_address, lockedEth, liquidity, isCycleNeeded = False, timestamp = None):
    for crypto in CRYPTO_ARRAY:
        query = '''
                             {
                              pools(first:1, orderBy: liquidity, orderDirection: desc,where:  { 
                    and:[ {totalValueLockedETH_gt: "''' + str(lockedEth) + '''"} {liquidity_gte: ''' + str(liquidity) + '''}
              {
                        or: [
                { token0: "''' + token_address + '''",
                  token1: "''' + crypto + '''"
                    },
                { token1: "''' + token_address + '''",
                  token0: "''' + crypto + '''"            
                    }
            ]        
              } 
            ] 
        }
        ) {
                       id
                       token0 {
                           symbol                    
                       }
                       token1 {
                           symbol
                       }
                       liquidity
          totalValueLockedETH
                   }}
                   '''



        response = requests.post(UNISWAP_V3_URL, json={'query': query})
        response_json = response.json()

        # Формируем список пулов для заданного токена
        pools = []
        if 'errors' not in response_json and response_json['data']['pools']:
            pair = response_json['data']['pools'][0]
            if isCycleNeeded and get_token_price_by_pair_and_timestamp_v3(pair['id'], timestamp, crypto) is None:
                continue
            pool = {
                'version': 'v3',
                'id': pair['id'],
                'token0': pair['token0']['symbol'],
                'token1': pair['token1']['symbol'],
                'liquidity': pair['liquidity'],
                'totalValueLockedETH': pair['totalValueLockedETH'],
                'compareTokenId': crypto
            }
            pools.append(pool)
            return pools[0]
    return None


# NEW
def get_valid_pair_for_token_v2(token_address, lockedEth, isCycleNeeded = False, timestamp = None):
    for crypto in CRYPTO_ARRAY:
        query = '''
               {
                              pairs(first:1, orderBy: reserveETH, orderDirection: desc,where:  { 
                    and:[
              {reserveETH_gt: "''' + str(lockedEth) + '''"}
              {
                        or: [
                { token0: "''' + token_address + '''",
                  token1: "''' + crypto + '''"
                    },
                { token1: "''' + token_address + '''",
                  token0: "''' + crypto + '''"

                    }
            ]        
              }

            ]

        }
        ) {
                       id
                       token0 {
                           symbol
                       }
                       token1 {
                           symbol
                       }
                       reserveETH
                   }
               }
               '''
        response = requests.post(UNISWAP_V2_URL, json={'query': query})
        response_json = response.json()

        # Формируем список пулов для заданного токена
        pools = []
        if 'errors' not in response_json and response_json['data']['pairs']:
            pair = response_json['data']['pairs'][0]
            # print(get_token_price_by_pair_and_timestamp_v2(pair['id'], timestamp, crypto))
            if isCycleNeeded and get_token_price_by_pair_and_timestamp_v2(pair['id'], timestamp, crypto) is None:
                continue
            pool = {
                'version': 'v2',
                'id': pair['id'],
                'token0': pair['token0']['symbol'],
                'token1': pair['token1']['symbol'],
                'reserveETH': pair['reserveETH'],
                'compareTokenId': crypto
            }
            pools.append(pool)
            return pools[0]
    return None


def get_token_price_by_pair_and_timestamp_v3(token_pair, timestamp=int(time.time()), compare_token=WETH_ADDRESS):
    query = '''
                {
        swaps(first:1, orderBy: timestamp, orderDirection: desc, where:
         { pool: "''' + token_pair.lower() + '''",
            timestamp_lte: ''' + str(timestamp) + ''',
            timestamp_gte: ''' + str(int(timestamp)-86400) + '''
        }
        ) {
          pool {
            token0 {
              id
              symbol
            }
            token1 {
              id
              symbol
            }
          }
          sender
          amountUSD
          recipient
          amount0
          amount1
          timestamp
         }
        }
    '''

    # print(compare_token)
    response = requests.post(UNISWAP_V3_URL, json={'query': query})
    response_json = response.json()
    if 'errors' not in response_json and response_json['data']['swaps']:
        swap = response_json['data']['swaps'][0]
        pool_obj = swap['pool']
        if pool_obj['token1']['id'] == compare_token:
            return abs(float(swap['amountUSD']) / float(swap['amount0']))
        elif pool_obj['token0']['id'] == compare_token:
            return abs(float(swap['amountUSD']) / float(swap['amount1']))
    return None


def get_token_price_by_pair_and_timestamp_v2(token_pair, timestamp=int(time.time()), compare_token=WETH_ADDRESS):
    query = '''
                {
        swaps(first:1, orderBy: timestamp, orderDirection: desc, where:
         { pair: "''' + token_pair.lower() + '''",
            timestamp_lte: ''' + str(timestamp) + ''',
            timestamp_gte: ''' + str(int(timestamp)-86400) + '''
        }
        ) {
          pair {
            token0 {
              id
              symbol
            }
            token1 {
              id
              symbol
            }
          }
         amount0In
         amount0Out
         amount1In
         amount1Out
         amountUSD
          timestamp
          transaction{
          id
          }
         }
        }
    '''
    response = requests.post(UNISWAP_V2_URL, json={'query': query})
    response_json = response.json()
    if 'errors' not in response_json and response_json['data']['swaps']:
        swap = response_json['data']['swaps'][0]
        pair_obj = swap['pair']

        swap_amount0In = float(swap['amount0In'])
        swap_amount1In = float(swap['amount1In'])
        swap_amount0Out = float(swap['amount0Out'])
        swap_amount1Out = float(swap['amount1Out'])
        swap_amountUSD = float(swap['amountUSD'])

        if pair_obj['token0']['id'] == compare_token:
            if swap_amount0In != 0.0 and swap_amount1Out != 0.0:
                return swap_amountUSD / swap_amount1Out
            elif swap_amount0Out != 0.0 and swap_amount1In != 0.0:
                return swap_amountUSD / swap_amount1In


        elif pair_obj['token1']['id'] == compare_token:
            if swap_amount0In != 0.0 and swap_amount1Out != 0.0:
                return swap_amountUSD / swap_amount0In
            elif swap_amount0Out != 0.0 and swap_amount1In != 0.0:
                return swap_amountUSD / swap_amount0Out

    return None


def get_token_price_by_token_address_and_timestamp_universal(token_address, isLockedEth, isCycleNeeded = False, timestamp=int(time.time())):
    if token_address in STABLE_COINS_ARR:
        return STABLE_COINS_ARR[token_address]
    # todo
    pair = get_valid_pool_v2v3(token_address, isLockedEth, isCycleNeeded, timestamp)
    print(pair)
    if pair:
        pair_address = pair['id']
        version = pair['version']
        if version == 'v3':
            tokenprice = get_token_price_by_pair_and_timestamp_v3(pair_address, timestamp, pair['compareTokenId'])
            # if tokenprice is None:
            #     v2pair = get_valid_pair_for_token_v2(token_address, 0)
            #     tokenprice = get_token_price_by_pair_and_timestamp_v2(v2pair['id'], timestamp,
            #                                                           pair['compareTokenId'])
            #     print(v2pair)
            #     print('ЗАХОДИМ В НАН БЛОК')
            # print(tokenprice)
            return tokenprice
        elif version == 'v2':

            return get_token_price_by_pair_and_timestamp_v2(pair_address, timestamp,
                                                            pair['compareTokenId'])
    return 0

#TODO если транза старая то цену не находит
def get_eth_price_by_timestamp(timestamp, vs_currency='ethusd'):
    if timestamp:
        v3_price = get_token_price_by_pair_and_timestamp_v3(WETH_USDC_PAIR_V3, timestamp, USDC_ADDRESS)
        if v3_price is None:
            return get_token_price_by_pair_and_timestamp_v2(WETH_USDC_PAIR_V2, timestamp, USDC_ADDRESS)
        else:
            return v3_price
    #TODO
    # get_token_price_by_token_address_and_timestamp_universal()
    # vs_currency='ethbtc'
    data = \
        requestGet(f'https://api.etherscan.io/api?module=stats&action=ethprice&apikey={ETHERSCAN_API_KEY}')['result'][
            vs_currency]
    if data:
        return float(data)
    else:
        return 0


# done
def get_token_price_by_transaction_hash_and_contract_address_v3(transaction_hash, contract_address):
    query = '''
                {
        swaps(where:
         {
						and: [
              {transaction: "''' + transaction_hash.lower() + '''"}
              {        	or:[
            {token0:"''' + contract_address.lower() + '''"}
            {token1:"''' + contract_address.lower() + '''"}
          ]}
            ]
        }
        ) {
          pool {
            token0 {
              id
              symbol
            }
            token1 {
              id
              symbol
            }
          }
          transaction{
            id
          }
          sender
          amountUSD
          recipient
          amount0
          amount1
          timestamp
         }
        	
        }
    '''
    response = requests.post(UNISWAP_V3_URL, json={'query': query})
    response_json = response.json()

    if response_json['data']['swaps']:
        swap = response_json['data']['swaps'][0]
        pool_obj = swap['pool']
        if pool_obj['token0']['id'] == contract_address:
            return abs(float(swap['amountUSD']) / float(swap['amount0']))
        elif pool_obj['token1']['id'] == contract_address:
            return abs(float(swap['amountUSD']) / float(swap['amount1']))
    return None


def get_token_price_by_transaction_hash_and_contract_address_v2(transaction_hash, contract_address):
    query = '''
                {
        swaps(where:
         {
						and: [
              {transaction: "''' + transaction_hash.lower() + '''"}
              {        	}
            ]
        }
        ) {
          pair {
            token0 {
              id
              symbol
            }
            token1 {
              id
              symbol
            }
          }
          transaction{
            id
          }
         amount0In
         amount0Out
         amount1In
         amount1Out
         amountUSD
          timestamp
         }
        	
        }
    '''
    response = requests.post(UNISWAP_V2_URL, json={'query': query})
    response_json = response.json()
    swaps = response_json['data']['swaps']
    if swaps:
        for swap in swaps:
            pair_obj = swap['pair']
            swap_amount0In = float(swap['amount0In'])
            swap_amount1In = float(swap['amount1In'])
            swap_amount0Out = float(swap['amount0Out'])
            swap_amount1Out = float(swap['amount1Out'])
            swap_amountUSD = float(swap['amountUSD'])
            if pair_obj['token1']['id'] == contract_address:
                if swap_amount0In != 0.0 and swap_amount1Out != 0.0:
                    return swap_amountUSD / swap_amount1Out
                elif swap_amount0Out != 0.0 and swap_amount1In != 0.0:
                    return swap_amountUSD / swap_amount1In

            elif pair_obj['token0']['id'] == contract_address:
                if swap_amount0In != 0.0 and swap_amount1Out != 0.0:
                    return swap_amountUSD / swap_amount0In
                elif swap_amount0Out != 0.0 and swap_amount1In != 0.0:
                    return swap_amountUSD / swap_amount0Out
    return None


def get_token_price_by_transaction_hash_and_contract_address_universal(transaction_hash, contract_address):
    v3 = get_token_price_by_transaction_hash_and_contract_address_v3(transaction_hash, contract_address)
    if v3:
        return v3
    else:
        v2 = get_token_price_by_transaction_hash_and_contract_address_v2(transaction_hash, contract_address)
        if v2:
            return v2
    return None


def get_trade_amountUSD_by_transaction_hash_and_contract_address_v3(transaction_hash, contract_address, realTokenValue):
    query = '''
                {
        swaps(where:
         {
						and: [
              {transaction: "''' + transaction_hash.lower() + '''"}
              {        	or:[
            {token0:"''' + contract_address.lower() + '''"}
            {token1:"''' + contract_address.lower() + '''"}
          ]}
            ]
        }
        ) {
          pool {
            token0 {
              id
              symbol
            }
            token1 {
              id
              symbol
            }
          }
          transaction{
            id
          }
          sender
          amountUSD
          recipient
          amount0
          amount1
          timestamp
         }

        }
    '''
    response = requests.post(UNISWAP_V3_URL, json={'query': query})
    response_json = response.json()

    swaps = response_json['data']['swaps']
    if swaps:
        amountUSD = 0
        for swap in swaps:
            if swap['sender'] != swap['recipient']:
                amountUSD += float(swap['amountUSD'])
            else:
                return get_token_price_by_transaction_hash_and_contract_address_v3(transaction_hash,
                                                                                   contract_address) * realTokenValue
        return amountUSD
    return None


def get_trade_amountUSD_by_transaction_hash_and_contract_address_v2(transaction_hash, contract_address, realTokenValue):
    query = '''
                {
        swaps(where:
         {
						and: [
              {transaction: "''' + transaction_hash.lower() + '''"}
              {        	}
            ]
        }
        ) {
          pair {
            token0 {
              id
              symbol
            }
            token1 {
              id
              symbol
            }
          }
          transaction{
            id
          }
         amount0In
         amount0Out
         amount1In
         amount1Out
         amountUSD
          timestamp
          sender
          to
         }

        }
    '''
    response = requests.post(UNISWAP_V2_URL, json={'query': query})
    response_json = response.json()
    swaps = response_json['data']['swaps']
    if swaps:
        amountUSD = 0
        for swap in swaps:
            pair_obj = swap['pair']
            if pair_obj['token0']['id'] == contract_address or pair_obj['token1']['id'] == contract_address:
                if swap['sender'] != swap['to']:
                    amountUSD += float(swap['amountUSD'])
                else:
                    return get_token_price_by_transaction_hash_and_contract_address_v2(transaction_hash,
                                                                                       contract_address) * realTokenValue
        return amountUSD
    return None


# TODO работает только для юнисвап, чекнуть апи других бирж
def get_trade_amountUSD_by_transaction_hash_and_contract_address_universal(transaction_hash, contract_address,
                                                                           realTokenValue):
    v3 = get_trade_amountUSD_by_transaction_hash_and_contract_address_v3(transaction_hash, contract_address,
                                                                         realTokenValue)
    if v3:
        return v3
    else:
        v2 = get_trade_amountUSD_by_transaction_hash_and_contract_address_v2(transaction_hash, contract_address,
                                                                             realTokenValue)
        if v2:
            return v2
    return 0


def get_trade_amountUSD_by_contract_address_and_timestamp_universal(contract_address, timestamp, realTokenValue,
                                                                    isLockedEth, isCycleNeeded):
    price = get_token_price_by_token_address_and_timestamp_universal(contract_address, isLockedEth, isCycleNeeded,
                                                                    timestamp)
    if price:
        return price * realTokenValue
    else:
        return 0
