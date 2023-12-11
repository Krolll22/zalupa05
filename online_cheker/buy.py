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

# Не меньше
a = 8
# Не больше
b = 100

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
        if a < percentage <= b:  # Можно изменить процентные значения в соответствии с вашими критериями
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
        if a < percentage <= b:
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
'0x2c9d5bd137ebeffecd59b3e2f21d6e9b1d604c41',
'0x08bd3bc9ded42a4a3c6ba300236a65183cf1033c',
'0x3d0ed8ee57e56482b6d5bd9e958aa4ba088d29ec',
'0x03cbe9e519c694241a958353e7a4b30a9c72bc91',
'0xbdb9ca80add74364d7b83c4ae1a35f7284e47815',
'0xb878f2580fe59ff608c3ac8788acfde983f1abce',
'0x9383cfd5bf6cb59addbd6b39c42dd137c50a8454',
'0x97be5745afb89b2a2a0ec92e922ffa3c971f5172',
'0xb1c57431ff506b7c51a94efcd15c489e4e7287cc',
'0x4d9df269b6831ac89e6a2bdb76e8d4e45c619d3d',
'0x7e8d2ec5ba735b57fdbd4573cb4250edc39e18c2',
'0xf71529c2a66d9ad77f10e47cf7206974c8cc5368',
'0xcf72296abac5c476c574a07c03ebeb5fbc86290e',
'0x2e390aace5fab542f48b77fede9af9071464adb9',
'0x19a4232cb77b518f87521aeab978626633faefc0',
'0x9e90ed1f9583ac054d7ded578b751076c640789f',
'0x36d4e14b4ddd4d3b216a0afa6f76e2643dce2936',
'0x04d933dbf480ebaea59758b577175b697fe64ff8',
'0xbaf8dfe5ccc428ed35d1c51d3f45ee5d566e445a',
'0x4df2e1e06281b25b4a88666aa247c288a26f2645',
'0x1361a72e2abba04c0d6fae7c4dd45821064d66d9',
'0x4a39f1a249dc55e099e29308fa6ee4d487252571',
'0x2e345889345e267a0893e5216b49c193406655de',
'0xa523829a5e7554604b9ad75901bf929d340d5a10',
'0x6f1657bcf3f57eb22f64286a07d91775def3d987',
'0xf8bba35258c292a9f99bcc05ed105f98f6a1be9f',
'0xbc2e380ffe5cb5ace5f1169138fea6e409baefdc',
'0xd68f718587af7b510f488b603d5bc80fdec5e048',
'0x3f3b7341e6e6c25f0ca0fc290007cffe8fcce37c',
'0xd481160f6a4441179b828fe8b192c3176fd4e7e8',
'0xf06f3fb6b984fe9bb71eddc7827baecad9cd2b5d',
'0xf408f9993df7129042400931bd138a04fb6d6b59',
'0xb4d4a9b91da967b7017a9bbd35aedb1590882d53',
'0x29f5d429b3bb9cd23fdf5960c5fc1cbb9031d688',
'0x4052fa8bd51bbaaa3875ce1240c86206c3057b85',
'0x4251de67ba4c39e29327f60b0be1ed442d3be663',
'0x8b5031b0956b64352ce7d6d5b29889af89c0c1e9',
'0x18f8cad4d6c7357271cb75bef07ca45a3537760f',
'0x8b1f929c88ab06f7f5fa03bd7f4f33bf3668a228',
'0xc9e2e81a28a01b554c4d97e9eff68375cc7c43c8',
'0x15b816e0d5aabbd5d21e59567f8f3570e6830613',
'0x544d3bcc8b1031d149e2fc65325860043230fb98',
'0xebbb46f1ff1b291b27ea81732b44b43d725dd242',
'0xaec1c63979209c1d642ff2d18d39a13122413556',
'0xef83ab8778542f4e162c477535766fbb97612af4',
'0x3a0375634cf93612576b7adcf1d766e9a9091805',
'0x660666f7a4792a75b5e79038f1327b8c2e7afbe5',
'0xe36afbd6bd71cbc4cf60a869755b9a40601fea13',
'0x6e7ffd47973d1909b6a1088231a8bdaacb43a684',
'0xb1b221aeed32074405831df06876da5dcf332283',
'0x5a5703a4afdb6ffab917162b7728ba8f891cf861',
'0x7561d9bd8259be296412ac10e8c57cd6d87f8092',
'0xbef2d1c03df924358a036a9e42167cfca3c8b380',
'0xba0608e2ecd747e14eecc5187b08ca9e4ddca188',
'0xc00550188754e8268a0387f84b05a53fa3f83eb3',
'0xc8826b6d38c406ccf9772111675406bb729fdb9e',
'0x886b7be01df0295d33c9a4b47cf217aa15b3e63f',
'0xd12586fee9b278176dea40f3ffc574003fa8e9d6',
'0x9c3ea7eb8f962fc63d252d985d923934cf9e0de7',
'0x2b1852ef2228d803118657386515e31b35ca74a7',
'0x6e2db2910e832413a1f59dc893363d6657ecdc43',
'0x73ea2535efbb30a24b56e443ff58e012468eeca5',
'0xc015ccc36e8b3e292b2742727ef4f59a2f560af2',
'0x38d045e6c44181d7d7277804749e3a922f8b10ab',
'0xf90d4a8756852df94a04487ce7249d721c4597bd',
'0xfe19e1b68380ef24fff763d67fd9d6d1b15774fe',
'0xecd20f88a0ae1de855c1190afb3ce731667e2b85',
'0x7b1867de2d19f9e4192654c824bc8705bd1015a8',
'0x6377e35902926c2339dc4e97a07294fda96eba6d',
'0x516a63b7ff4782d1e17c66c6fa6de7cbcad75299',
'0x76a895917522abd54894781edbf70ad563673227',
'0x4c26f8470063de3ad8a7c72728434b4dc94d743a',
'0x0edc72f437b659527f6394192d1eaa6e77f5dab6',
'0x0abb3e0505bcfcac7c2b7d021339ecd19f1a00b7',
'0xc3aa6e968ddeed2ea414d9a93de57df6deb8e196',
'0xe214c39e0adbd251cbc08eaf217c693f236b9071',
'0xe2e66b5f4e1d12f509092caacd42961bf653f238',
'0xbc0db1b983c78f27cb7a25cb0c69a87a33862828',
'0x446c6d422910a3d7fe87e1bb5e4f88faa29432ee',
'0xe426a732552764f3301dedf98014ad880a74ce51',
'0xcac91124d9898423860b28a9bd9b9997e2d01144',
'0x21bde9ca6a7875628f96091ed56c202b36e48ec0',
'0x4863a7828cc2d0f89fde10dc5b65ef4502c7cd85',
'0xaf32f66d9c8155ae618da559c20b9492a13304cc',
'0x67435556708011de58a664a2219e4fe69349844c',
'0xc91437295ef30c710c26c4e7b2ea00b43801d8ce',
'0xb8f09851f2369050e0ddce37c987ae74cb44212f',
'0xd7f382c0b1631e81ac73d0abd5f6f37613d44ef9',
'0x58b2e7b23187def4de572ca4950c9cb7787c786c',
'0x9eaf842de8d1378ec63dbc9289b47d200ac8794d',
'0xde391fb3b3458c6de1538c1ea0ebfb854b8ca068',
'0x837c9c56088610167a326f70ac21ba2cfc2b9bf9',
'0x5dd8207a3fff97e5c088b8c1ea84d4aad8bca9ba',
'0xa306d7b8dd0b142e68df3834aff648c3b9215171',
'0x96d6d9624abb4020f13c50724368510591b278b2',
'0x355e63426362d5a7e6eb102dd9c3c289f8e8ff8a',
'0xa29cf8252323a1f3c2c19c14e48a194c023b35de',
'0xe6ab0517bdc0393eb1551fb1ef419dfc00f9ae2a',
'0x96d3f98e431175d35db5f3586d0ba1450c6d28dd',
'0xe51829cad94ed7ec3e1c33d105bb42e4b03007f3',
'0x985c85bc1eaecee6c7b3e418374447cf4852266c',
'0xb1e19b7105ef97a0b7ad272589c0fd98dcad614d',
'0x12128876c6ea20c3af84963cc3e528729a3718a2',
'0xd30b3a727f48e916074902469ad88ee5ab37bbce',
'0x38075b539b6ce0f8fabbd66af35dc6864602b8e8',
'0xa832b7f6d628a2474cead883b85bf84ad3bb0517',
'0xf9f664b5a75777e7b6b515480cb7cb7e145493db',
'0x1a297afb9373355bb9492e469ca0a531fda87364',
'0x819af5b6957702ebf7a336644b3901c7215a2512',
'0x5618179840d22f68e938cbd1e9c281a0a1a5adcf',
'0xd2a83431ba3b3c595af30c2d1f05d1124702480d',
'0x28f278ac605c976df44e5e889f6ba612d8af3748',
'0xe65504f6eb76bcd143b9e4c9145161453cf12be2',
'0x486df957b5650b139d519d8cca5e357e6cc5f269',
'0x1ed46d05ea302c93824b1cc7ca51b970078ee448',
'0x4fc03e24dbf2b51b5417aff6d070054362342ecf',
'0xd8192ad29b2667ee3e2f9be2ed73707aa6f295f9',
'0x7e1d726dd28f65e8f50f109b209f2f6321660d10',
'0x8fa05caee3ca6d32e45bcc20848f3c0607beb4f4',
'0x0f27f672d7ab745d9f4a9d973140f69179e8fd84',
'0x3347867b260c67420967939e6414277a1de84302',
'0x7eb6fa8b4432f8e665b2e3b450b25a641f8a0d21',
'0x369635a54c1e6d98b1c269748b425c68cc2ed2f2',
'0x2203cca2cefe50101134e4330249fcd5a4f39d72',
'0xf35c6b18cd05eb2f1e23a0051960f742b7cf449f',
'0xd06b438f2ca6bd498780c8499a0b08ba4e8d07d6',
'0x57cb30c98930a3b926f849620b3bd96dd0ca6911',
'0x71582d5d7d72feda7a524c3fb4c2c66bb9fc3ea3',
'0x003a598070368f98f96612e0029b989b7bd990b2',
'0x2ec229e81144b48d7f596f6a4952ffaf7f86e904',
'0xb29e1f5f24fd40680063ac312fd2674ae99c71ec',
'0x8b8b689f9035bbe262d64b5c3c4613e481f7d716',
'0x9b8b584f434a52f2849ba3d3e67c856757c8aa02',
'0x7c1141a94f1d04d4de4fb4e0b308117f13ce280a',
'0x62abeddd874bf39bcc4b76d61d639b0b728fcd20',
'0x6488566a1cff7b791542c98c09a053bdde164f9a',
'0x3b7214f0162a437b0f502c84d7251a7141f72dd0',
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
