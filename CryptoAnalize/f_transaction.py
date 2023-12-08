import requests

from f_const import ETHERSCAN_URL, ETHERSCAN_API_KEY


def get_transaction_logs_by_hash(tx_hash):
    payload = {"module": "proxy", "action": "eth_getTransactionReceipt", "txhash": tx_hash, "apikey": ETHERSCAN_API_KEY}
    response = requests.get(ETHERSCAN_URL, params=payload).json()
    if response["result"]["logs"]:
        return response["result"]["logs"]
    else:
        return None
