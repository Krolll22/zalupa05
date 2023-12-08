from datetime import datetime

import requests
from moralis import evm_api

from f_const import WALLET_ADDRESS, MORALIS_API_KEY, ETHERSCAN_API_KEY, ETH_COFF, MAX_TXNS_COUNT, STABLE_COINS_ARR
from f_http_request import requestGet
from f_tokens import get_token_price_by_token_address_and_timestamp_universal, get_eth_price_by_timestamp, \
    get_trade_amountUSD_by_contract_address_and_timestamp_universal
from f_transaction import get_transaction_logs_by_hash
from f_utils import print_divider


def get_ethBalance(wallet_address=WALLET_ADDRESS):
    json_data = requestGet(
        f'https://api.etherscan.io/api?module=account&action=balance&address={wallet_address}&tag=latest&apikey={ETHERSCAN_API_KEY}')
    return float(json_data['result']) / ETH_COFF


# faster
def moralis_get_account_tokensInfo(address=WALLET_ADDRESS):
    params = {
        "address": address,
        "chain": "eth",
    }

    account_tokens = evm_api.token.get_wallet_token_balances(
        api_key=MORALIS_API_KEY,
        params=params,
    )
    #
    # #balance = 0
    # print("Токены:")
    # for item in account_tokens:
    #     item['realBalance'] = float(item['balance']) / 10 ** item['decimals']
    #     print(f"- {item}")
    # pr = get_tokenPrice_universal(item['token_address'])
    # print(pr)
    # balance += (float(item['balance']) / 10 ** item['decimals'])
    return account_tokens


def get_txInternal_byHash(txn_hash, wallet_address=WALLET_ADDRESS):
    value = 0

    # # URL для запроса информации о транзакции
    # url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={txn_hash}&apikey={etherscan_api_key}"
    #
    # # Отправляем GET-запрос
    # response = requests.get(url)
    #
    # # Распарсим JSON
    # json_data = json.loads(response.text)

    # Выводим информацию о транзакции
    # print(f"Hash транзакции: {json_data['result']['hash']}")
    # print(f"Отправитель: {json_data['result']['from']}")
    # print(f"Получатель: {json_data['result']['to']}")
    # print(f"Количество эфира: {int(json_data['result']['value'], 16) / ethCoff} ETH")
    # print(f"Дата: {json_data['result']['timeStamp']}")

    print(f"Hash транзакции: {txn_hash}")

    # URL для запроса внутренних транзакций
    url = f"https://api.etherscan.io/api?module=account&action=txlistinternal&txhash={txn_hash}&apikey={ETHERSCAN_API_KEY}"

    # Отправляем GET-запрос
    response = requests.get(url)

    # Выводим информацию о внутренних транзакциях

    value = 0
    if response.status_code == 200:
        json_data = response.json()
        print("     Внутренние транзакции:")
        if json_data["status"] == "1":
            for txn in json_data["result"]:
                if txn['to'].lower() == wallet_address.lower():
                    print(int(txn['value']))
                    value = int(txn['value'])
                    print(f"    От: {txn['from']}, Кому: {txn['to']}, Количество: {int(txn['value']) / ETH_COFF} ETH")
                    return value  # / ethCoff
                else:
                    print("***транзакция не подходит")
                    print(f"    От: {txn['from']}, Кому: {txn['to']}, Количество: {int(txn['value']) / ETH_COFF} ETH")
        else:
            print("Ошибка получения данных:", json_data["message"])
            return value
    else:
        print("Ошибка отправки запроса:", response.status_code)
        return value
    return value


def get_txns_and_acc_info(wallet_address=WALLET_ADDRESS):
    # URL-адрес API для получения списка транзакций
    url = f'https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&sort=asc&apikey={ETHERSCAN_API_KEY}'

    # Выполнение запроса GET к API
    response = requests.get(url)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Получение данных в формате JSON
        data = response.json()
        print(data)
        # Проверка наличия транзакций
        if data['status'] == '1' and data['result']:
            total_profit = 0
            # Перебор транзакций и вывод информации
            for tx in data['result']:
                print_divider()
                # Получение даты транзакции
                tx_date = datetime.fromtimestamp(int(tx['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S')
                # if tx_date < '2022-10-16':
                #     continue
                tx['type'] = "outgoing"
                if int(tx['value']) == 0:
                    tx['type'] = "incoming"
                    tx['value'] = get_txInternal_byHash(tx['hash'])
                if tx['isError'] == '1':
                    print(f"Транзакция {tx['hash']} завершилась с ошибкой.")
                    continue
                if tx['to'].lower() == wallet_address.lower():
                    print(f"Транзакция {tx['hash']} получения.")
                    continue
                # Получение цены ETH на момент проведения транзакции
                tx_url = f'https://api.etherscan.io/api?module=stats&action=ethprice&apikey={ETHERSCAN_API_KEY}'
                tx_response = requests.get(tx_url)
                if tx_response.status_code == 200:
                    tx_data = tx_response.json()
                    if tx_data['status'] == '1':
                        eth_price = float(tx_data['result']['ethusd'])
                    else:
                        print('Ошибка при получении цены ETH.')
                        break
                else:
                    print('Ошибка при выполнении запроса к API.')
                    break

                # Расчет стоимости транзакции

                eth_amount = float(tx['value']) / ETH_COFF
                transaction_value = eth_amount * eth_price
                if tx['type'] == "outgoing":
                    total_profit -= transaction_value
                elif tx['type'] == "incoming":
                    total_profit += transaction_value

                # Вывод информации о транзакции

                print(
                    f"Date: {tx_date} | {tx['type']} | TxHash: {tx['hash']} | From: {tx['from']} | To: {tx['to']} | Value: {int(tx['value']) / ETH_COFF} | Balance: {total_profit:.2f} ")

            # Вывести общий профит по операциям
            print_divider()
            # print(f"Acc profit: {total_profit+get_account_tokensInfo()} USD")
            print_divider()
        else:
            print('Нет транзакций для этого адреса.')
    else:
        print('Ошибка при выполнении запроса к API.')


def get_token_transactions_by_wallet(wallet_address=WALLET_ADDRESS):
    url = f'https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&startblock=0&endblock=99999999&&sort=asc&apikey={ETHERSCAN_API_KEY}'
    response = requests.get(url).json()
    token_transactions = response['result']
    return token_transactions


def get_eth_transactions_by_wallet(wallet_address=WALLET_ADDRESS):
    url = f'https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&sort=asc&apikey={ETHERSCAN_API_KEY}'
    response = requests.get(url).json()
    eth_transactions = response['result']
    return eth_transactions


def eth_getTransactionCount(wallet_address=WALLET_ADDRESS):
    json_data = requestGet(
        f'https://api.etherscan.io/api?module=proxy&action=eth_getTransactionCount&address={wallet_address}&tag=latest&apikey={ETHERSCAN_API_KEY}')
    return int(json_data['result'], 16)


def account_is_valid(wallet_address=WALLET_ADDRESS):
    if eth_is_wallet(wallet_address):
        if eth_getTransactionCount(wallet_address) > MAX_TXNS_COUNT:
            return bool(False)
        return bool(True)
    return False


def eth_is_wallet(wallet_address=WALLET_ADDRESS):
    json_data = requestGet(
        f'https://api.etherscan.io/api?module=proxy&action=eth_getCode&address={wallet_address}&tag=latest&apikey={ETHERSCAN_API_KEY}')
    if json_data["result"] != "0x":
        return bool(False)
    else:
        return bool(True)


def get_account_tokens_balance_moralis(wallet_for_check):
    tokens = moralis_get_account_tokensInfo(wallet_for_check)
    tokens_amountUSD = 0
    for token in tokens:
        token['realBalance'] = float(token['balance']) / 10 ** token['decimals']
        tokens_amountUSD += get_token_price_by_token_address_and_timestamp_universal(token['token_address'], True,
                                                                                     True) * token[
                                'realBalance']
        print(f'{token} tokens_amountUSD = {tokens_amountUSD}')
    tokens_amountUSD += get_ethBalance(wallet_for_check) * get_eth_price_by_timestamp(None)
    return tokens_amountUSD


def get_account_eth_balance(wallet_for_check):
    balanceETH = 0
    eth_txns = get_eth_transactions_by_wallet(wallet_for_check)
    for txn in eth_txns:
        if txn['isError'] == '1':
            continue
        else:
            if txn['input'] == '0x':
                # print(txn)
                realTokenValue = int(txn['value']) / ETH_COFF
                price = get_eth_price_by_timestamp(txn['timeStamp'])
                tradePrice = 0
                if txn['to'] == wallet_for_check:
                    tradePrice = price * realTokenValue * -1
                elif txn['from'] == wallet_for_check:
                    tradePrice = price * realTokenValue
                # print(tradePrice)
                balanceETH += tradePrice
    return balanceETH


def get_account_token_profit(wallet_for_check):
    balance = 0
    token_txns = get_token_transactions_by_wallet(wallet_for_check)
    for txn in token_txns:
        print_divider()
        print(txn)
        txn_hash = txn['hash'].lower()
        if len(get_transaction_logs_by_hash(txn_hash)) == 1:
            print('##PRIHOD YHOD##')
            txn_contractAddress = txn['contractAddress'].lower()
            realTokenValue = int(txn['value']) / 10 ** int(txn['tokenDecimal'])
            if txn_contractAddress in STABLE_COINS_ARR:
                price = STABLE_COINS_ARR[txn_contractAddress]
                tradePrice = 0
                if txn['to'] == wallet_for_check:
                    tradePrice = price * realTokenValue * -1
                elif txn['from'] == wallet_for_check:
                    tradePrice = price * realTokenValue
                balance += tradePrice
                print(tradePrice)
                print(balance)
                continue
            else:
                # print('вызов метода get_trade_amountUSD_by_transaction_hash_and_contract_address_universal')
                amountUSD = get_trade_amountUSD_by_contract_address_and_timestamp_universal(txn_contractAddress,
                                                                                            txn['timeStamp'],
                                                                                            realTokenValue, False, True)
                if txn['to'] == wallet_for_check:
                    balance -= amountUSD
                    print(amountUSD * -1)
                elif txn['from'] == wallet_for_check:
                    balance += amountUSD
                    print(amountUSD)
                print(balance)
            print_divider()
        else:
            print('##OBMEN##')

    print_divider()
    return balance
