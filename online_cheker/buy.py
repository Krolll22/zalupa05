from multiprocessing import connection
import requests
from datetime import datetime
import time
import sqlite3
import telegram
from datetime import datetime, timedelta, timezone
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup
import threading

bot = telegram.Bot(token='6014113590:AAGlrJ_YwykcgAkCiROyXivqTSFeqPwZ8ZM')
chat_id = '463825725'

def fetch_data_from_db():
    conn = sqlite3.connect('info.db')
    cursor = conn.cursor()
    # Измените запрос для объединения данных из таблиц buy_token и sale_token
    query = '''
        SELECT 
            b.token_symbol, 
            b.from_address, 
            b.count, 
            b.percent AS buy_percent, 
            s.percent AS sale_percent
        FROM buy_token b
        LEFT JOIN sale_token s ON b.token_symbol = s.token_symbol AND b.from_address = s.to_address
    '''
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def create_db_connection():
    connection = sqlite3.connect('info.db')
    return connection

def create_table(connection):
    cursor = connection.cursor()
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS buy_token (
        token_symbol TEXT,
        from_address TEXT,
        count INTEGER,
        percent REAL
    )'''
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()

def clear_table(connection):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM buy_token")
    connection.commit()
    cursor.close()

def insert_into_buy_token(connection, token_symbol, from_address, count, percent):
    cursor = connection.cursor()
    insert_query = '''
    INSERT INTO buy_token (token_symbol, from_address, count, percent)
    VALUES (?, ?, ?, ?)'''
    cursor.execute(insert_query, (token_symbol, from_address, count, percent))
    connection.commit()
    cursor.close()

def insert_into_sale_token(connection, token_symbol, to_address, count, percent):
    cursor = connection.cursor()
    insert_query = '''
    INSERT INTO sale_token (token_symbol, to_address, count, percent)
    VALUES (?, ?, ?, ?)'''
    cursor.execute(insert_query, (token_symbol, to_address, count, percent))
    connection.commit()
    cursor.close()

# Создание и очистка таблицы для продаж (если необходимо)
def create_sale_table(connection):
    cursor = connection.cursor()
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS sale_token (
        token_symbol TEXT,
        to_address TEXT,
        count INTEGER,
        percent REAL
    )'''
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()

def create_daily_info_table(connection):
    cursor = connection.cursor()
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS daily_info (
        date TEXT,
        token_symbol TEXT,
        from_address TEXT,
        to_address TEXT,
        count INTEGER,
        buy_percent REAL,
        sale_percent REAL
    )'''
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()

def clear_sale_table(connection):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM sale_token")
    connection.commit()
    cursor.close()

def clear_daily_table(connection):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM daily_info")
    connection.commit()
    cursor.close()

connection = create_db_connection()

create_table(connection)
create_sale_table(connection)
create_daily_info_table(connection)
clear_daily_table(connection)
clear_table(connection)
clear_sale_table(connection)

def clear_files():
    open('output_buy.txt', 'w').close()

last_update_time = None
data_processing_completed = False

def safe_send_message(bot, chat_id, message):
    max_length = 4096  # Максимальная длина сообщения в Telegram

    while message:
        # Отправляем часть сообщения и удаляем её из оригинальной строки
        bot.send_message(chat_id, message[:max_length])
        message = message[max_length:]

def compare_and_send_new_tokens(bot, chat_id, connection):
    cursor = connection.cursor()

    # Получаем токены из buy_token
    cursor.execute("SELECT token_symbol, from_address FROM buy_token")
    buy_tokens = set(cursor.fetchall())

    # Получаем токены из daily_info
    cursor.execute("SELECT token_symbol, from_address FROM daily_info")
    daily_info_tokens = set(cursor.fetchall())

    # Находим новые токены, которые есть в buy_token, но нет в daily_info
    new_tokens = buy_tokens - daily_info_tokens

    if new_tokens:
        message = "New tokens found:\n"
        for token_symbol, from_address in new_tokens:
            message += f"Token Symbol: {token_symbol}, From: {from_address}\n"

        # Используем функцию безопасной отправки
        safe_send_message(bot, chat_id, message)
    else:
        bot.send_message(chat_id, "No new tokens found")

    cursor.close()

def copy_data_to_daily_info(connection):
    cursor = connection.cursor()

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Проверяем, были ли данные уже вставлены сегодня
    if not check_if_data_already_inserted(connection):
        # Копирование данных из buy_token в daily_info
        copy_query = '''
        INSERT INTO daily_info (date, token_symbol, from_address, count, buy_percent)
        SELECT ?, token_symbol, from_address, count, percent FROM buy_token
        '''
        cursor.execute(copy_query, (today,))
        connection.commit()
        print("Data copied to daily_info for", today)
    else:
        print("Data already inserted for", today)

    cursor.close()

def send_data(bot, chat_id):
    data = fetch_data_from_db()
    message = ""
    for row in data:
        token_symbol, from_address, count, buy_percent, sale_percent = row
        # Форматирование процента покупки
        buy_percent_text = f"{buy_percent:.2f}%" if buy_percent is not None else "0.00%"

        # Добавление информации о проценте продажи только если она доступна
        if sale_percent is not None:
            sale_percent_text = f" Percent.exit: {sale_percent:.2f}%"
        else:
            sale_percent_text = ""

        line = f"Token Symbol: {token_symbol}, Count: {count}, Percent: {buy_percent_text}{sale_percent_text}\n"

        if len(message) + len(line) > 4096:
            bot.send_message(chat_id, message)
            message = line
        else:
            message += line

    if message:
        bot.send_message(chat_id, message)
    else:
        bot.send_message(chat_id, "No data available")

def check_if_data_already_inserted(connection):
    cursor = connection.cursor()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM daily_info WHERE date = ?", (today,))
    count = cursor.fetchone()[0]
    cursor.close()
    return count > 0

def is_wallet_address_valid(address, network, api_keys):
    network_urls = {
        'ethereum': "https://api.etherscan.io/api",
        'bnb': "https://api.bscscan.com/api",
        'arbitrum': "https://api.arbiscan.io/api",
        'polygon': "https://api.polygonscan.com/api"
    }
    url = f"{network_urls[network]}?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={api_keys[network]}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1' and data['result']:
            last_transaction = data['result'][0]
            last_transaction_date = datetime.fromtimestamp(int(last_transaction['timeStamp']), timezone.utc)
            return datetime.now(timezone.utc) - last_transaction_date <= timedelta(days=7)
    return False


def get_latest_token_sales(api_keys, address, network, unique_tokens):
    network_urls = {
        'ethereum': "https://api.etherscan.io/api",
        'bnb': "https://api.bscscan.com/api",
        'arbitrum': "https://api.arbiscan.io/api",
        'polygon': "https://api.polygonscan.com/api"
    }

    url = f"{network_urls[network]}?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={api_keys[network]}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1' and data['result']:
            transactions = data['result']
            for tx in transactions:
                if tx['from'].lower() == address.lower():
                    token_info = (tx['tokenSymbol'], tx['to'])
                    if token_info not in unique_tokens[address]:
                        unique_tokens[address].add(token_info)
                        print(f"Address: {address}, Network: {network}, Token: {tx['tokenSymbol']}, To: {tx['to']}")
    else:
        print(f"Failed to connect to {network} API for wallet {address}")

def process_sales_transactions(unique_tokens):
    with open('output_sale.txt', 'w', encoding='utf-8') as file:
        for address, tokens in unique_tokens.items():
            file.write(f"Unique token sales for wallet {address}:\n")
            for token_symbol, to_address in tokens:
                file.write(f"Token Symbol: {token_symbol}, To: {to_address}\n")
            file.write("-" * 60 + "\n")

def analyze_sales_data(wallet_addresses, connection):
    token_to_counts = {}

    with open('output_sale.txt', 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith('Token Symbol:'):
                token_symbol_part, to_part = line.strip().split(", ")
                token_symbol = token_symbol_part.split(": ")[1]
                to_address = to_part.split(": ")[1]
                key = (token_symbol, to_address)
                token_to_counts[key] = token_to_counts.get(key, 0) + 1

    wallet_addresses_count = len(wallet_addresses)

    for (token_symbol, to_address), count in token_to_counts.items():
        percentage = (count / wallet_addresses_count) * 100
        if 6 < percentage <= 90:  # Можно изменить процентные значения в соответствии с вашими критериями
            insert_into_sale_token(connection, token_symbol, to_address, count, percentage)

def get_latest_token_purchases(api_keys, address, network, unique_tokens):
    network_urls = {
        'ethereum': "https://api.etherscan.io/api",
        'bnb': "https://api.bscscan.com/api",
        'arbitrum': "https://api.arbiscan.io/api",
        'polygon': "https://api.polygonscan.com/api"
    }

    url = f"{network_urls[network]}?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={api_keys[network]}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1' and data['result']:
            transactions = data['result']
            for tx in transactions:
                if tx['to'].lower() == address.lower():
                    token_info = (tx['tokenSymbol'], tx['from'])
                    if token_info not in unique_tokens[address]:
                        unique_tokens[address].add(token_info)
                        print(f"Address: {address}, Network: {network}, Token: {tx['tokenSymbol']}, From: {tx['from']}")
    else:
        print(f"Failed to connect to {network} API for wallet {address}")

def process_transactions(unique_tokens):
    with open('output_buy.txt', 'w', encoding='utf-8') as file:
        for address, tokens in unique_tokens.items():
            file.write(f"Unique token purchases for wallet {address}:\n")
            for token_symbol, from_address in tokens:
                file.write(f"Token Symbol: {token_symbol}, From: {from_address}\n")
            file.write("-" * 60 + "\n")

def analyze_data(wallet_addresses, connection):
    token_from_counts = {}

    # Чтение и анализ данных из файла output_buy.txt
    with open('output_buy.txt', 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith('Token Symbol:'):
                token_symbol_part, from_part = line.strip().split(", ")
                token_symbol = token_symbol_part.split(": ")[1]
                from_address = from_part.split(": ")[1]
                key = (token_symbol, from_address)
                token_from_counts[key] = token_from_counts.get(key, 0) + 1

    # Расчет процента от общего количества адресов
    wallet_addresses_count = len(wallet_addresses)

    # Анализ и запись результатов
    for (token_symbol, from_address), count in token_from_counts.items():
        percentage = (count / wallet_addresses_count) * 100
        if 6 < percentage <= 90:
            insert_into_buy_token(connection, token_symbol, from_address, count, percentage)

def start(update, context):
    
    keyboard = [
        [telegram.KeyboardButton("Send Processed Data")],
        [telegram.KeyboardButton("Check New Tokens")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text("Version bot 1.0, Choose an option:", reply_markup=reply_markup)

    # Запуск основного цикла в фоновом потоке
    thread = threading.Thread(target=main_loop)
    thread.start()
    update.message.reply_text("Bot started!")

def data_button_handler(update, context):
    global data_processing_completed
    if data_processing_completed:
        send_data(bot, chat_id)
        data_processing_completed = True  # Сброс флага после отправки данных
    else:
        update.message.reply_text("Data processing is still in progress. Please wait.")

def button_handler(update, context):
    global data_processing_completed

    if data_processing_completed:
        compare_and_send_new_tokens(bot, chat_id, create_db_connection())
        data_processing_completed = True  # Сброс флага после отправки сообщения
    else:
        update.message.reply_text("Data processing is still in progress. Please wait.")

def main():
    # Создание объекта Updater и привязка токена бота
    updater = Updater("6014113590:AAGlrJ_YwykcgAkCiROyXivqTSFeqPwZ8ZM", use_context=True)

    # Получение диспетчера для регистрации обработчиков
    dp = updater.dispatcher

    # Регистрация команды start
    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(MessageHandler(Filters.text("Send Processed Data") & ~Filters.command, data_button_handler))
    dp.add_handler(MessageHandler(Filters.text("Check New Tokens") & ~Filters.command, button_handler))

    # Запуск бота
    updater.start_polling()
    updater.idle()

def main_loop():

    global data_processing_completed
    global last_update_time
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    while True:

        connection = create_db_connection()

        clear_table(connection)
        clear_sale_table(connection)

        # Предварительно определенный список адресов
        wallet_addresses = [
        '0x84ccbf403370bbd060fe1f5ac88b5d5a44a2154f',
        '0xb022613d2b438df9b46ba426313d7bf69f49d9a2',
        '0xcf0d458ab8a54ef8d35b8b1b7713bfd8f412a9be',
        '0x09b0123bfdadb230511b256cf61176d339538c25',
        '0x0d7b8c6cb7cb9f16f5ec8d89472a504abb3df751',
        '0x13df64e9ec7b05d49812b6f1a1c28f7cfe213d24',
        '0x13e80af6e25bc608864b3a589c2e6c93f9415912',
        ]

        start_time = time.time()

        api_keys = {
            'ethereum': 'KKJMDJBAZIXY1W379K2J89MFHHJRS1BP1B',
            'bnb': 'AHP8K2Q14MZFSH2VDXAYXY8U4ZP3RB3NI2',
            'arbitrum': 'E5RVS4B695DJ4GQZZK7Y2GWKEUBX5MWR8S',
            'polygon': 'HAPKBIMDF2CZCWQM2Y53PF9X43JSMBAXTM'
        }

        networks = ['ethereum', 'bnb', 'arbitrum', 'polygon']

        unique_sales = {}
        unique_tokens = {}

        for address in wallet_addresses:
            unique_sales[address] = set()
            unique_tokens[address] = set()
            for network in networks:
                # Проверяем валидность адреса перед обработкой
                if is_wallet_address_valid(address, network, api_keys):
                    get_latest_token_sales(api_keys, address, network, unique_sales)
                    get_latest_token_purchases(api_keys, address, network, unique_tokens)
                else:
                    print(f"Address {address} in network {network} is not valid. Skipping.")

        process_transactions(unique_tokens)
        analyze_data(wallet_addresses, connection)
        process_sales_transactions(unique_sales)
        analyze_sales_data(wallet_addresses, connection)

        current_time = time.time()

        if not last_update_time or current_time - last_update_time >= 86400:  # 86400 секунд в сутках
            copy_data_to_daily_info(connection)
            last_update_time = current_time

        end_time = time.time()
        print(f"Execution time: {end_time - start_time} seconds")
        connection.close()

        data_processing_completed = True

        bot.send_message(chat_id, f"It is finish work script, Execution time: {end_time - start_time} seconds, Current time: {today}")

        time.sleep(300)

if __name__ == '__main__':
    main()


# while True:
#     # Предварительно определенный список адресов
#     wallet_addresses = [
#     '0x84ccbf403370bbd060fe1f5ac88b5d5a44a2154f',
#     '0xb022613d2b438df9b46ba426313d7bf69f49d9a2',
#     '0xcf0d458ab8a54ef8d35b8b1b7713bfd8f412a9be',
#     '0x09b0123bfdadb230511b256cf61176d339538c25',
#     '0x0d7b8c6cb7cb9f16f5ec8d89472a504abb3df751',
#     '0x13df64e9ec7b05d49812b6f1a1c28f7cfe213d24',
#     ]


#     start_time = time.time()

#     api_keys = {
#         'ethereum': 'KKJMDJBAZIXY1W379K2J89MFHHJRS1BP1B',
#         'bnb': 'AHP8K2Q14MZFSH2VDXAYXY8U4ZP3RB3NI2',
#         'arbitrum': 'E5RVS4B695DJ4GQZZK7Y2GWKEUBX5MWR8S',
#         'polygon': 'HAPKBIMDF2CZCWQM2Y53PF9X43JSMBAXTM'
#     }

#     networks = ['ethereum', 'bnb', 'arbitrum', 'polygon']
#     unique_sales = {}
#     unique_tokens = {}

#     for address in wallet_addresses:
#         unique_sales[address] = set()
#         unique_tokens[address] = set()
#         for network in networks:
#             # Проверяем валидность адреса перед обработкой
#             if is_wallet_address_valid(address, network, api_keys):
#                 get_latest_token_sales(api_keys, address, network, unique_sales)
#                 get_latest_token_purchases(api_keys, address, network, unique_tokens)
#             else:
#                 print(f"Address {address} in network {network} is not valid. Skipping.")
               
#     clear_table(connection)
#     clear_sale_table(connection)
#     process_transactions(unique_tokens)
#     analyze_data(wallet_addresses, connection)
#     process_sales_transactions(unique_sales)
#     analyze_sales_data(wallet_addresses, connection)

#     current_time = time.time()
#     if not last_update_time or current_time - last_update_time >= 86400:  # 86400 секунд в сутках
#         copy_data_to_daily_info(connection)
#         last_update_time = current_time

#     if __name__ == '__main__':
#         send_data(bot, chat_id)
#         end_time = time.time()
#         print(f"Execution time: {end_time - start_time} seconds")
#         main()

#     time.sleep(600)