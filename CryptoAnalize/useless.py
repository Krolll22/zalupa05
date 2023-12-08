#
# # useless
# def get_liquidity_for_pool_v3(pool_address):
#     # Запрос к Uniswap V3 API для получения информации о пуле
#     query = '''
#     {
#       pools(where: { id: "''' + pool_address + '''" }) {
#         id
#         token0 {
#           symbol
#         }
#         token1 {
#           symbol
#         }
#         liquidity
#       }
#     }
#     '''
#     response = requests.post(UNISWAP_V3_URL, json={'query': query})
#     response_json = response.json()
#
#     # Формируем информацию о ликвидности для заданного пула
#     pool = response_json['data']['pools'][0]
#     return int(pool['liquidity'])
#
#
# # useless
# def get_liquidity_for_pool_v2(pair_address):
#     url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
#     query = """
#         query {{
#             pair(id: "{pair_address}"){{
#
#                 volumeUSD
#             }}
#         }}
#         """.format(pair_address=pair_address)
#     response = requests.post(url, json={'query': query})
#
#     if response.status_code == 200:
#         return response.json()['data']['pair']['volumeUSD']
#     else:
#         raise Exception("Unable to retrieve Uniswap V2 pair data.")
#
#
# # useless
# def get_pools_for_token_v3(token_address):
#     UNISWAP_V3_URL = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
#
#     query = '''
#     {
#       pools(where: { token0: "''' + token_address + '''" }) {
#         id
#         feeTier
#         token0 {
#           symbol
#         }
#         token1 {
#           symbol
#         }
#       }
#     }
#     '''
#
#     response = requests.post(UNISWAP_V3_URL, json={'query': query})
#     response_json = json.loads(response.text)
#
#     # Формируем список пулов для заданного токена
#     pools = []
#     for pair in response_json['data']['pools']:
#         id = pair['id']
#         pool = {
#             'version': 'v3',
#             'id': id,
#             'token0': pair['token0']['symbol'],
#             'token1': pair['token1']['symbol'],
#             'liquidity': get_liquidity_for_pool_v3(id)
#         }
#         pools.append(pool)
#
#     for item in pools:
#         print(item)
#     return pools
#
#
# # useless
# def get_pools_for_token_v2(token_address):
#     # Задайте адрес Uniswap V2 API
#     UNISWAP_V2_URL = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2'
#     # Запрос к Uniswap V2 API для получения списка пулов, где указанный токен является токеном 0
#     # token 1\0
#     query = '''
#            {
#                pairs(where: {token0: "''' + token_address + '''"}) {
#                    id
#                    token0 {
#                        symbol
#                    }
#                    token1 {
#                        symbol
#                    }
#                    reserveETH
#                }
#            }
#            '''
#     response = requests.post(UNISWAP_V2_URL, json={'query': query})
#     response_json = response.json()
#
#     # Формируем список пулов для заданного токена
#     pools = []
#     for pair in response_json['data']['pairs']:
#         id = pair['id']
#         pool = {
#             'version': 'v2',
#             'id': id,
#             'token0': pair['token0']['symbol'],
#             'token1': pair['token1']['symbol'],
#             'liquidity': get_liquidity_for_pool_v2(id),
#             'reserveETH': pair['reserveETH']
#         }
#         pools.append(pool)
#     for item in pools:
#         print(item)
#     return pools