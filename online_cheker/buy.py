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
from telegram import Bot
from telegram.utils.request import Request

data_processing_completed = False

request = Request(connect_timeout=300.0, read_timeout=300.0)
bot = Bot(token='6014113590:AAGlrJ_YwykcgAkCiROyXivqTSFeqPwZ8ZM', request=request)

chat_ids = ['463825725', '274000220']

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

def create_archive_data_table(connection):
    cursor = connection.cursor()
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS archive_data (
        token_symbol TEXT,
        from_address TEXT,
        count INTEGER,
        buy_percent REAL
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

def clear_archive_table(connection):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM archive_data")
    connection.commit()
    cursor.close()

connection = create_db_connection()

create_archive_data_table(connection)
create_table(connection)
create_sale_table(connection)
create_daily_info_table(connection)
clear_daily_table(connection)
clear_table(connection)
clear_sale_table(connection)

def clear_files():
    open('output_buy.txt', 'w').close()

last_update_time = None

def compare_archive_data(connection):
    cursor = connection.cursor()
    # Получаем данные из archive_data
    cursor.execute("SELECT token_symbol, from_address, count FROM archive_data")
    archive_data = cursor.fetchall()
    
    # Получаем данные из daily_info
    cursor.execute("SELECT token_symbol, from_address FROM daily_info")
    daily_info_data = cursor.fetchall()

    # Преобразуем данные из daily_info в set для ускорения поиска
    daily_info_set = { (token_symbol, from_address) for token_symbol, from_address in daily_info_data }

    # Формируем список токенов, которые есть в archive_data, но нет в daily_info
    new_tokens = [row for row in archive_data if (row[0], row[1]) not in daily_info_set]

    cursor.close()
    return new_tokens

def send_compare_archive_data(bot, chat_ids, connection):
    data_to_send = compare_archive_data(connection)
    if not data_to_send:
        for chat_id in chat_ids:
            bot.send_message(chat_id, "No data avalible")
        return

    messages = format_archive_data_for_message(data_to_send)
    for message in messages:
        safe_send_message(bot, chat_ids, message)

def button_handler_archive_data(update, context):
    connection = create_db_connection()
    try:
        send_compare_archive_data(context.bot, chat_ids, connection)
    finally:
        connection.close()

def entry_archive_data(connection):
    cursor = connection.cursor()
    # Получаем данные из buy_token
    cursor.execute("SELECT * FROM buy_token")
    data_to_archive = cursor.fetchall()
    
    if data_to_archive:
        # Очищаем таблицу archive_data и записываем новые данные
        cursor.execute("DELETE FROM archive_data")
        insert_query = "INSERT INTO archive_data (token_symbol, from_address, count, buy_percent) VALUES (?, ?, ?, ?)"
        cursor.executemany(insert_query, data_to_archive)
        connection.commit()
        print("Data successfully archived.")
    else:
        print("No data to archive.")
    
    cursor.close()

def format_archive_data_for_message(data):
    messages = []
    message = ""
    for token_symbol, from_address, count in data:
        line = f"Token Symbol: {token_symbol}, From: {from_address}, Count: {count}\n"
        if len(message) + len(line) > 4000:
            messages.append(message)
            message = line
        else:
            message += line
    if message:
        messages.append(message)
    return messages

def send_archive_data(connection, bot, chat_ids):
    cursor = connection.cursor()
    # Получаем данные из archive_data
    cursor.execute("SELECT token_symbol, count, buy_percent FROM archive_data")
    data = cursor.fetchall()
    cursor.close()

    if not data:
        print("No archived data to send.")
        return

    # Форматируем данные для отправки
    messages = format_archive_data_for_message(data)
    for message in messages:
        safe_send_message(bot, chat_ids, message)

def safe_send_message(bot, chat_ids, message):
    max_length = 4096
    for chat_id in chat_ids:
        temp_message = message
        while temp_message:
            bot.send_message(chat_id, temp_message[:max_length])
            temp_message = temp_message[max_length:]

def compare_data(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM buy_token")
    buy_token_data = cursor.fetchall()
    
    cursor.execute("SELECT token_symbol, from_address FROM daily_info")
    daily_info_data = cursor.fetchall()
    
    daily_info_set = set(tuple(i[:2]) for i in daily_info_data)  # Consider only token_symbol and from_address
    
    # Find entries in buy_token not in daily_info
    result = [data for data in buy_token_data if (data[0], data[1]) not in daily_info_set]
    cursor.close()
    return result

def format_messages(differences):
    message = ""
    messages = []
    for diff in differences:
        line = f"Token Symbol: {diff[0]}, From Address: {diff[1]}, Count: {diff[2]}, Percent: {diff[3]}\n"
        if len(message) + len(line) > 4000:
            messages.append(message)
            message = line
        else:
            message += line
    if message:  # Add any remaining message text
        messages.append(message)
    return messages

def send_compare_data(bot, chat_ids, connection):
    differences = compare_data(connection)
    messages = format_messages(differences)
    
    for message in messages:
        for chat_id in chat_ids:
            bot.send_message(chat_id=chat_id, text=message)

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

def send_data(bot, chat_ids):
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
            # Отправляем текущее сообщение всем пользователям и начинаем новое сообщение
            for chat_id in chat_ids:
                bot.send_message(chat_id, message)
            message = line
        else:
            message += line

    if message:
        for chat_id in chat_ids:
            bot.send_message(chat_id, message)
    else:
        for chat_id in chat_ids:
            bot.send_message(chat_id, message)

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
        if 3 < percentage <= 25:  # Можно изменить процентные значения в соответствии с вашими критериями
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
        if 3 < percentage <= 25:
            insert_into_buy_token(connection, token_symbol, from_address, count, percentage)

def start(update, context):
    
    keyboard = [
        [telegram.KeyboardButton("Send Processed Data")],
        [telegram.KeyboardButton("Check New Tokens")],
        [telegram.KeyboardButton("Send Archive Data")],
        [telegram.KeyboardButton("Compare Archive Data")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text("Version bot 1.0, Choose an option:", reply_markup=reply_markup)

    # Запуск основного цикла в фоновом потоке
    thread = threading.Thread(target=main_loop)
    thread.start()
    update.message.reply_text("Bot started!")

def send_archive_data_button_handler(update, context):
    connection = create_db_connection()
    try:
        send_archive_data(connection, bot, chat_ids)
    finally:
        connection.close()

def data_button_handler(update, context):
    global data_processing_completed

    if data_processing_completed:
        send_data(bot, chat_ids)
    else:
        update.message.reply_text("Data processing is still in progress. Please wait.")

def button_handler(update, context):
    global data_processing_completed

    if data_processing_completed:
        send_compare_data(bot, chat_ids, create_db_connection())
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
    dp.add_handler(MessageHandler(Filters.text("Send Archive Data") & ~Filters.command, send_archive_data_button_handler))
    dp.add_handler(MessageHandler(Filters.text("Compare Archive Data") & ~Filters.command, button_handler_archive_data))

    # Запуск бота
    updater.start_polling()
    updater.idle()

def main_loop():

    global data_processing_completed
    global last_update_time
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    while True:
        data_processing_completed = False

        connection = create_db_connection()

        clear_table(connection)
        clear_sale_table(connection)

        # Предварительно определенный список адресов
        wallet_addresses = [
'0x95374a34a55143b9c5b57efeeeda6e39843fbab9',
'0xbaf8dfe5ccc428ed35d1c51d3f45ee5d566e445a',
'0xa2c04c13ede1e6b514c301e0fb02e23a01df331c',
'0xc517c84b82a9a74419bba85faac584b3e7adb705',
'0xcfd0ab22fc62e2c166c57197dfeb488715ea77e9',
'0x3b563f592c88a37fdc97c63e3287e916cd6918a4',
'0xe50c4588b3135ae73cfe7faed0bda17ef1f911aa',
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

        data_processing_completed = True

        if data_processing_completed:
            entry_archive_data(connection)

        end_time = time.time()
        print(f"Execution time: {end_time - start_time} seconds")
        connection.close()

        for chat_id in chat_ids:
            bot.send_message(chat_id, f"It is finish work script, Execution time: {end_time - start_time} seconds, Current time: {today}")

        time.sleep(120)

if __name__ == '__main__':
    main()
