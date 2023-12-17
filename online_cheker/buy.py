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

tracking_requests = {}

api_keys = {
            'ethereum': 'KKJMDJBAZIXY1W379K2J89MFHHJRS1BP1B',
            'bnb': 'AHP8K2Q14MZFSH2VDXAYXY8U4ZP3RB3NI2',
            'arbitrum': 'E5RVS4B695DJ4GQZZK7Y2GWKEUBX5MWR8S',
            'polygon': 'HAPKBIMDF2CZCWQM2Y53PF9X43JSMBAXTM'
        }

wallet_addresses = [
'0x003a598070368f98f96612e0029b989b7bd990b2',
'0x0171d947ee6ce0f487490bd4f8d89878ff2d88ba',
'0x025ca319047228155a56c53930f6cea0e9f06642',
'0x034d93faa6a7d53fb5937fc8e646c2699caf73b0',
'0x04d933dbf480ebaea59758b577175b697fe64ff8',
'0x05cb7ef70eb203416a19ec3f1a4558fe69d758d6',
'0x0804be3e8debf26e085313edb2c9318f6b792ec5',
'0x090c8f45be37c6d782786b783992d56a779df599',
'0x0bc75f7e24161d0491c128a271e455ad69b4bc63',
'0x0e2ad0c14a5842dcd5e58d2d600d1e027d19f8ce',
'0x0f5739385ddd4b26e274255d6fc51480aa68ebee',
'0x105b8d22e620ccf1bddb10cd1d411cde06cb529a',
'0x1155e35c5868f7b98f15830ef2555cb9156de02e',
'0x12128876c6ea20c3af84963cc3e528729a3718a2',
'0x13119a518b96cb640c1d2447259f90fb44a39391',
'0x1361a72e2abba04c0d6fae7c4dd45821064d66d9',
'0x16705d6b3fb9398eb239970c124db15967a6f33e',
'0x18f8cad4d6c7357271cb75bef07ca45a3537760f',
'0x19a4232cb77b518f87521aeab978626633faefc0',
'0x1a297afb9373355bb9492e469ca0a531fda87364',
'0x1c23a4f454e71e029e62158c3527103d7cbf962a',
'0x1c8a49e361844557218561993df296445c130c02',
'0x1c99bc0545ad440abc43a708d4b049342a5acc39',
'0x1cb7b06f6b6e8b4b69b8a33942ce96c68bce717c',
'0x1d2dbcfc2a9a0bea739e643bf0d6330fd0dca921',
'0x1d837df2cfe874b3d3f0a663de3892e62cef3b99',
'0x1da35b7b703934b183cce3ade9dc18784c7707c7',
'0x1dcefafd64f41c81c83df135b1a5c555cc8679a0',
'0x205421497ef6bb3f724ffe237e2e196d970d104a',
'0x212d396e78d753ed23dd8720abd6377a5dad09af',
'0x264514e884c9449eb1979e17364f472bdfd37dc0',
'0x28a4c3b2fd93c06c16efb3582381ba89eaf7fd36',
'0x28baa6966682a1cfe049592cfdaf930d714450c8',
'0x29f5d429b3bb9cd23fdf5960c5fc1cbb9031d688',
'0x2af469688de783c68373197fb181e5eb90a9baaf',
'0x2b1852ef2228d803118657386515e31b35ca74a7',
'0x2be37f1e6e3195af1e1e926d05fbb1facc61c9cf',
'0x2e345889345e267a0893e5216b49c193406655de',
'0x303e60a17981110e5dccf58c0babcac6f92c71cf',
'0x32add1e77702a3726364fa64d0096d194fdf99f5',
'0x355e63426362d5a7e6eb102dd9c3c289f8e8ff8a',
'0x35670de0c60e5c297163d2191df69479472f4345',
'0x38075b539b6ce0f8fabbd66af35dc6864602b8e8',
'0x38d045e6c44181d7d7277804749e3a922f8b10ab',
'0x3a21b89bd8653eeda5437a97a5feb476e180d1c3',
'0x3a34ffc6506b56f1457ff31fc7d92678da4c70f6',
'0x3b00059d1f13c4dd1162d688b80d5b6e5620aec8',
'0x3b7214f0162a437b0f502c84d7251a7141f72dd0',
'0x3d0ed8ee57e56482b6d5bd9e958aa4ba088d29ec',
'0x3deed1cc348c07382a876b3d23864598e2a6aeaa',
'0x3f3b7341e6e6c25f0ca0fc290007cffe8fcce37c',
'0x4052fa8bd51bbaaa3875ce1240c86206c3057b85',
'0x415aef4585f74eaf9a7fde46cb0f68576b506e32',
'0x4330e0919e21cb4b51d6e26aed8e888dc3cda686',
'0x446c6d422910a3d7fe87e1bb5e4f88faa29432ee',
'0x46815c8b3b11b96d52dfb6b281593c7368094e7a',
'0x48f52f5df2f7ef2a49d376e250a49a4a9c054e1b',
'0x4aea59297683e572a65628f58b06d75ef5a3cea8',
'0x4b906981a4ca9c0b2eb18b59a6c029cfc120d308',
'0x4c26f8470063de3ad8a7c72728434b4dc94d743a',
'0x4ce13cbea39252ddcd82d33dce3948bbebef98a1',
'0x4ceb2bbeb33b409786038991699d90a6371c5602',
'0x4dcdddaa351af1017a05a4f4965223f7db9246f8',
'0x4f5d03b4b4df519ab495fffdf3e40de5edeadff8',
'0x4fc03e24dbf2b51b5417aff6d070054362342ecf',
'0x50bd15765ce37d01f0a63e0b7fa59997df54d056',
'0x5146933e048fa94bde51b4c13f78a01cfc58f956',
'0x51778284c6e5f3e859e8d0252b0493dab470b2b6',
'0x519f0b0e151a13854f5c85415ab3449012e6c8b6',
'0x5238ba01a77b6a31ab355c6cc1682834b87424bc',
'0x529ddb6d75514c399efa2339b6e858222ed3598a',
'0x53c2803bdfc0d7b52c950414a5bb55633e718b94',
'0x544d3bcc8b1031d149e2fc65325860043230fb98',
'0x5529d17553d8387ae6dfa50bcf35b60539f93dcc',
'0x55e49a7ba0ebf8fc5b21941078e062a86b2ccb68',
'0x55ef26fbe77e1373eb133b50949985bfe3f64efe',
'0x5618179840d22f68e938cbd1e9c281a0a1a5adcf',
'0x58b2e7b23187def4de572ca4950c9cb7787c786c',
'0x5ab4c45896687bab14bbf73b78765e6dfac795ac',
'0x6042716c272e2f4094a781fa20b7fba8cf090639',
'0x61f5e68675846170fd4720fdb24b28676c633c10',
'0x624893c30b62f4f37de4702c7a557bb9e8f4e51d',
'0x62abeddd874bf39bcc4b76d61d639b0b728fcd20',
'0x631bc81de34c359da5f021946dd3d9e72f32880e',
'0x6377e35902926c2339dc4e97a07294fda96eba6d',
'0x6488566a1cff7b791542c98c09a053bdde164f9a',
'0x658d18ffad5d1bd4113c668eb5ccc86cf5b710a9',
'0x660666f7a4792a75b5e79038f1327b8c2e7afbe5',
'0x67148e1daf1587b8a885b68ba2e71d59549b45ce',
'0x67b581da8c894a38b1f375054f250a4b0f45aa26',
'0x6a025880e87d0a14419f50b8f5011b268f9456f3',
'0x6ab3d4820d2a39a3895f0abebb8b2caf980876bb',
'0x6c095c72c1da7755ce3838ecc3c3c42ce3461e98',
'0x6f1657bcf3f57eb22f64286a07d91775def3d987',
'0x70a5b4d1d974b991686091d3b981844308079ead',
'0x717b85ad0cf6813a9bae0911435f302d38561d5c',
'0x73ea2535efbb30a24b56e443ff58e012468eeca5',
'0x74dc418cd9bf7b42a93b9c8fafa2878242394ba8',
'0x7767e1bdf16a6d2a5b8218f707c28695d6a47ea1',
'0x79ccda7ce3f3e4b9fd5622778a2345230d6c735b',
'0x7b60c0aac0db8445fd5a760f538281da3aa3c78e',
'0x7cab2fbf5283c11539ee6052891a03da177204db',
'0x7defcf28a656d0b3624a0f2b7e45a4da65c1a80d',
'0x7e8d2ec5ba735b57fdbd4573cb4250edc39e18c2',
'0x7ebb5c7748430cffba86d0aa8fdafef48ffd2583',
'0x7ebcc50319fef70ebd584715f137441cdaed7b20',
'0x7f1bf82a3f83ad0b38f33394256eb4bff51ca258',
'0x837c9c56088610167a326f70ac21ba2cfc2b9bf9',
'0x83a6b1d844132defc166d7b0c3df7063c61715cd',
'0x85823b63cc6c3d87a77c405982ef919214a9e44d',
'0x88b989d62feb70a687ff8c383d1cd83d247bf6a6',
'0x8b1486fc0b093b261ed97e14f6831f3ac4b71899',
'0x8b1f929c88ab06f7f5fa03bd7f4f33bf3668a228',
'0x8ca07dea1af35ee1c8fb9bf605f9fe74f6b52e77',
'0x8ccd2f9a736f571128cee447c026f8ef05e1e939',
'0x8da81929b80a0f0d6a407411b75abb7e09a0ea80',
'0x8e5d897f3dc32e4304f6d06f0345ddb1a125656a',
'0x8f937aa7495fe9b23e08d99f2a0cc3a73f400dc6',
'0x91f6b363cf7f55a445d3ff3d8f1a7a07c3030100',
'0x93db59e48b2f5271e2ae101a222069693533e614',
'0x96d6d9624abb4020f13c50724368510591b278b2',
'0x9c8f2b0f9998af782eb4e50e444ede4997fc1873',
'0x9d9774d2415061747b3b3c33b0b0147671869c21',
'0x9eaf842de8d1378ec63dbc9289b47d200ac8794d',
'0x9eb2cb03b1fcae8afd82de7ffa73d2ff1e776fcc',
'0xa097ace28a160b52aee34decdddfc677b95af28e',
'0xa2125b9b854e98aa414530a4bf2384c09b1cbd0d',
'0xa29cf8252323a1f3c2c19c14e48a194c023b35de',
'0xa2eb7b6397a2d98c1241e6dec18a5d78cda3bebc',
'0xa4bdb8d08792dcf5af79d371df8d59c6ebb5d752',
'0xa523829a5e7554604b9ad75901bf929d340d5a10',
'0xa5493506ef4395fff9b780c81acf88ba3e0a8575',
'0xb1ea8b6b65d2d9a553ec995e9915cc10fa000e56',
'0xb2fe283c54e6acec5b0240a50d8c4d6de121af9c',
'0xb4d4a9b91da967b7017a9bbd35aedb1590882d53',
'0xb83c0a77076cac4ad3d804e2134a3819a21f68c8',
'0xb85516fe2d99cff2061863b46945085e43acf9da',
'0xb878f2580fe59ff608c3ac8788acfde983f1abce',
'0xb8b253451797d517592249825a6db06314c6c079',
'0xba8a2046261e703156abbf34399af1cd4e041be7',
'0xbbfa7688cdca899b9ec36b8b4654b0fea7aa2436',
'0xbc0db1b983c78f27cb7a25cb0c69a87a33862828',
'0xbc2e380ffe5cb5ace5f1169138fea6e409baefdc',
'0xbce4f2ba047bfd2d10e4f22a9b991de793625c8d',
'0xbdadbfdebc59ff8cd9bf3d6aff2d844f46a50858',
'0xbdbf71e69c97f0409819831c2da6da4083552a3e',
'0xbef2d1c03df924358a036a9e42167cfca3c8b380',
'0xc015ccc36e8b3e292b2742727ef4f59a2f560af2',
'0xc096822893b23639c0a875bab24c2bb8ca4dbe47',
'0xc2393180993312a3d8f5ca26da036d8bd050d98b',
'0xc8ddb827c3f11e8fe36e717ef84cc9a9d36f6672',
'0xc9e2e81a28a01b554c4d97e9eff68375cc7c43c8',
'0xca71bfc3f2dcf50f7a6e978b3c9b8514875ee605',
'0xcac91124d9898423860b28a9bd9b9997e2d01144',
'0xcff7c5093abcc36eb0819921602bd24dfd663f84',
'0xd12586fee9b278176dea40f3ffc574003fa8e9d6',
'0xd2a83431ba3b3c595af30c2d1f05d1124702480d',
'0xd73782247e525e48787391f6ac700ba668b7b09a',
'0xd79770efb72ff38a8a8cef4fbd8ffdf11478c69e',
'0xd7a4f3dd5a4086b58d9913d75740a19f46140784',
'0xd7ba122762f3dedd1fc805c9b72f2e6dbca909b4',
'0xd7f382c0b1631e81ac73d0abd5f6f37613d44ef9',
'0xdd7defae2aca7db74d075b8425a1549d65e50003',
'0xdf1a9bcd5e5bd99cd2227225783142420a232d23',
'0xe01ee5a59032c7499d40430676effd689cafb144',
'0xe0fede5531b6605e18625b8ef867c1b861a0c99d',
'0xe1ba910e83576221d119489582f55359357d9edd',
'0xe36afbd6bd71cbc4cf60a869755b9a40601fea13',
'0xe426a732552764f3301dedf98014ad880a74ce51',
'0xe6ab0517bdc0393eb1551fb1ef419dfc00f9ae2a',
'0xe714eaa394cd5924bfd42ea3b4179edd0813ce6a',
'0xe78948dbc55414c241671202ed5f05439e8fa951',
'0xe8ee136e53afcb2ffe77e4401ba436ea6653dfae',
'0xe9372b7ad7e2c56b3ed7e4e0491926635104195e',
'0xe98a6d8794ccddded528ef7c1845920aad906df4',
'0xecd20f88a0ae1de855c1190afb3ce731667e2b85',
'0xee9b2581df06967490ad2080fa65a4ad87a7f2a3',
'0xf0d02605bbae7d625bb0a486720bf39be0f465be',
'0xf1ba09bf15cc219b66f44693a95aba7f4bd1c12f',
'0xf408f9993df7129042400931bd138a04fb6d6b59',
'0xf4d3bdabcfe1e8646a06b735cf7958c4b4cdd9ec',
'0xf8bba35258c292a9f99bcc05ed105f98f6a1be9f',
'0xf90d4a8756852df94a04487ce7249d721c4597bd',
'0xf9bf8d7c207034bc8efa923e639a26a9f8d5056c',
'0xf9f664b5a75777e7b6b515480cb7cb7e145493db',
'0xf9f664b5a75777e7b6b515480cb7cb7e145493db',
'0xfa3342da6937139f45eec6f41f3e56a0791ad89d',
'0xfd07d7fda5673f3b5605859a8cd97f60108612cb',
'0xfe0c6286c7afad92aebf43bc2c74cf9a44bf95e3',
'0xfe8daf020635bbb63f239cfd8a1eb81296c1f4c3',
'0xff46bc0a888233028915b6ce84d6209092ba9b58',
'0xffa06227dd8a9350cfc03eeb5387130deec79bc4',
        ]

# Не меньше
a = 60
# Не больше
b = 100

data_processing_completed = False

request = Request(connect_timeout=300.0, read_timeout=300.0)
bot = Bot(token='6014113590:AAGlrJ_YwykcgAkCiROyXivqTSFeqPwZ8ZM', request=request)

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

def send_compare_archive_data(bot, chat_id, connection):
    data_to_send = compare_archive_data(connection)
    if not data_to_send:
        bot.send_message(chat_id, "No data avalible")
        return

    messages = format_archive_data_for_message(data_to_send)
    for message in messages:
        safe_send_message(bot, chat_id, message)

def button_handler_archive_data(update, context):
    chat_id = update.message.chat_id
    connection = create_db_connection()
    try:
        send_compare_archive_data(context.bot, chat_id, connection)
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
        line = f"Token Symbol: {token_symbol}, Count: {from_address}, Percent: {count}\n"
        if len(message) + len(line) > 4000:
            messages.append(message)
            message = line
        else:
            message += line
    if message:
        messages.append(message)
    return messages

def send_archive_data(connection, bot, chat_id):
    cursor = connection.cursor()
    # Получаем данные из archive_data
    cursor.execute("SELECT token_symbol, count, buy_percent FROM archive_data")
    data = cursor.fetchall()
    cursor.close()

    if not data:
        bot.send_message(chat_id, "No archived data to send.")
        return

    # Форматируем данные для отправки
    messages = format_archive_data_for_message(data)
    for message in messages:
        safe_send_message(bot, chat_id, message)

def safe_send_message(bot, chat_id, message):
    max_length = 4096
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

def send_compare_data(bot, chat_id, connection):
    differences = compare_data(connection)
    messages = format_messages(differences)
    
    for message in messages:
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
            # Отправляем текущее сообщение всем пользователям и начинаем новое сообщение
            bot.send_message(chat_id, message)
            message = line
        else:
            message += line

    if message:
        bot.send_message(chat_id, message)
    else:
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
            return datetime.now(timezone.utc) - last_transaction_date <= timedelta(days=2)
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
    chat_id = update.message.chat_id
    
    keyboard = [
        [telegram.KeyboardButton("Send Processed Data")],
        [telegram.KeyboardButton("Check New Tokens")],
        [telegram.KeyboardButton("Send Archive Data")],
        [telegram.KeyboardButton("Compare Archive Data")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text("Version bot 1.0, Choose an option:", reply_markup=reply_markup)

    # Запуск основного цикла в фоновом потоке
    thread = threading.Thread(target=main_loop, args=(chat_id,))
    thread.start()
    update.message.reply_text("Bot started!")

def send_archive_data_button_handler(update, context):
    connection = create_db_connection()
    try:
        chat_id = update.message.chat_id
        send_archive_data(connection, context.bot, chat_id)
    finally:
        connection.close()

def data_button_handler(update, context):
    chat_id = update.message.chat_id
    global data_processing_completed

    if data_processing_completed:
        send_data(bot, chat_id)
    else:
        update.message.reply_text("Data processing is still in progress. Please wait.")

def button_handler(update, context):
    global data_processing_completed
    chat_id = update.message.chat_id

    if data_processing_completed:
        send_compare_data(context.bot, chat_id, create_db_connection())
    else:
        update.message.reply_text("Data processing is still in progress. Please wait.")

def track(update, context):
    args = context.args
    chat_id = update.message.chat_id

    if len(args) != 2:
        update.message.reply_text("Usage: /track <token_symbol> <from_address>")
        return

    token_symbol, from_address = args
    tracking_token = (token_symbol, from_address)

    # Сохраняем запрос в словаре
    tracking_requests[chat_id] = {'token': tracking_token, 'active': True}

    # Запускаем цикл анализа данных в отдельном потоке
    thread = threading.Thread(target=analyze_loop, args=(chat_id,))
    thread.start()

def analyze_loop(chat_id):
    while tracking_requests.get(chat_id, {}).get('active', False):
        tracking_token = tracking_requests[chat_id]['token']
        analyze_and_send_results(tracking_token, chat_id)
        time.sleep(5)  # Задержка 20 секунд

    # Очищаем запрос из словаря после остановки цикла
    if chat_id in tracking_requests:
        del tracking_requests[chat_id]

# Функция для остановки цикла анализа данных
def stop_tracking(update, context):
    chat_id = update.message.chat_id
    if chat_id in tracking_requests:
        tracking_requests[chat_id]['active'] = False
        update.message.reply_text("Tracking stopped.")
    else:
        update.message.reply_text("No active tracking to stop.")


def analyze_and_send_results(tracking_token, chat_id):
    global wallet_addresses
    global api_keys
    network_urls = {
        'ethereum': "https://api.etherscan.io/api",
        'bnb': "https://api.bscscan.com/api",
        'arbitrum': "https://api.arbiscan.io/api",
        'polygon': "https://api.polygonscan.com/api"
    }
    unique_tokens = {}
    for address in wallet_addresses:
        unique_tokens[address] = set()
        for network in network_urls.keys():
            if is_wallet_address_valid(address, network, api_keys):
                get_latest_token_purchases(api_keys, address, network, unique_tokens)

    # Запись уникальных токенов в файл
    with open('track_out.txt', 'w', encoding='utf-8') as file:
        for address, tokens in unique_tokens.items():
            for token_symbol, from_address in tokens:
                file.write(f"{address},{token_symbol},{from_address}\n")

    # Анализ файла для нахождения совпадений
    matching_wallets = 0
    with open('track_out.txt', 'r', encoding='utf-8') as file:
        for line in file:
            _, token_symbol, from_address = line.strip().split(',')
            if (token_symbol, from_address) == tracking_token:
                matching_wallets += 1

    # Расчет процента совпадений
    percentage = (matching_wallets / len(wallet_addresses)) * 100

    # Отправка результатов в чат
    result_message = f"Token: {tracking_token[0]}, Count: {matching_wallets}, Percentage: {percentage:.2f}%"
    bot.send_message(chat_id, result_message)

def help(update, context):
    help_message = (
        "All commands:\n"
        "/start - Start the bot and analysis.\n"
        "/track [token_symbol] [from] - Start tracking specific token transactions.\n"
        "/stop_t - Stop the ongoing tracking process.\n"
        "/help - Get help for bot management assistance."
    )
    update.message.reply_text(help_message)

def main():
    # Создание объекта Updater и привязка токена бота
    updater = Updater("6014113590:AAGlrJ_YwykcgAkCiROyXivqTSFeqPwZ8ZM", use_context=True)

    # Получение диспетчера для регистрации обработчиков
    dp = updater.dispatcher

    # Регистрация команды start
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("track", track, pass_args=True))
    dp.add_handler(CommandHandler("stop_t", stop_tracking))
    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(MessageHandler(Filters.text("Send Processed Data") & ~Filters.command, data_button_handler))
    dp.add_handler(MessageHandler(Filters.text("Check New Tokens") & ~Filters.command, button_handler))
    dp.add_handler(MessageHandler(Filters.text("Send Archive Data") & ~Filters.command, send_archive_data_button_handler))
    dp.add_handler(MessageHandler(Filters.text("Compare Archive Data") & ~Filters.command, button_handler_archive_data))

    # Запуск бота
    updater.start_polling()
    updater.idle()

def main_loop(chat_id):

    global data_processing_completed
    global last_update_time
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    while True:
        data_processing_completed = False

        connection = create_db_connection()

        clear_table(connection)
        clear_sale_table(connection)

        # Предварительно определенный список адресов
        global wallet_addresses

        start_time = time.time()

        global api_keys

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
            send_compare_data(bot, chat_id, create_db_connection())

        end_time = time.time()
        print(f"Execution time: {end_time - start_time} seconds")
        connection.close()

        bot.send_message(chat_id, f"It is finish work script, Execution time: {end_time - start_time} seconds, Current time: {today}")

        time.sleep(120)

if __name__ == '__main__':
    main()
