# ETH WALLET ADDRESS
WALLET_ADDRESS = '0x0a2458e20485c23F7dD9BC8fDbC0E01c495A09c3'.lower()

# для отсева скам монет
TOKEN_PRICE_MAX = 20000

# def get_valid_pair_for_token_v2(token_address)
TOKEN_RESERVE_ETH_MIN = 5
# def get_valid_pair_for_token_v3(token_address)
TOTAL_VALUE_LOCKED_ETH_MIN = 5

# API KEYS
ETHERSCAN_API_KEY = 'KKJMDJBAZIXY1W379K2J89MFHHJRS1BP1B'
MORALIS_API_KEY = 'MCPGyT2xMMuPFmqlQkxJ8fsg5Qw9JlfKt6oxe7EYYJjJhwABtiFVNWLdKQkWmmYV'

# Etherscan API endpoint
ETHERSCAN_URL = "https://api.etherscan.io/api"

#  Uniswap API
UNISWAP_V2_URL = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2'
UNISWAP_V3_URL = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'

# ETH decimal coff
ETH_COFF = (10 ** 18)

# WETH ADDRESS
WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'.lower()
USDC_ADDRESS = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'.lower()
USDT_ADDRESS = '0xdac17f958d2ee523a2206206994597c13d831ec7'.lower()
WETH_USDC_PAIR_V3 = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'.lower()
WETH_USDC_PAIR_V2 = '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'.lower()

# фильтр для отсева по колву транз
MAX_TXNS_COUNT = 200

STABLE_COINS_ARR = {
    #USDT
    '0xdac17f958d2ee523a2206206994597c13d831ec7': 1,
    #USDC
    '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 1
}

CRYPTO_ARRAY = [WETH_ADDRESS, USDC_ADDRESS, USDT_ADDRESS]