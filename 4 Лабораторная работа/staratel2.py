import re
import subprocess, sys, keyboard


def ExCommands(textComands, communic):
    return subprocess.Popen(textComands, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate(communic)


def AddRoleAccount(folderId, serviceId, role):
    prog_config = ['powershell', f'yc resource-manager folder add-access-binding {folderId} '
                                 f'--subject serviceAccount:{serviceId} '
                                 f'--role {role}']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def YcInitAccount(name, token):
    comm = b"2\n%b\n%b\n1\n\n2\n" % (name, token)
    ExCommands(['powershell', 'yc init'], comm)
    print('Успех')
    menu()


def YcList():
    result = str(ExCommands(['powershell', 'yc config list --format yaml'], ''))
    print(result)
    token = str(*re.findall('(token: [0-9a-zA-Z_-]*)', result)).replace('token: ', '')
    print("Токен аккаунта:", token)
    menu()


def CreateFirstFunc():
    print("Создание первой функции")
    prog_config = ['powershell',
                   'yc serverless function create --name my-first-function']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    text = ('''def handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello World!',
    }''')

    file = open('index.py', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    prog_config = ['powershell', 'yc iam service-account get --name service-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)

    prog_config = ['powershell',
                   'yc serverless function version create '
                   '--function-name my-first-function '
                   '--memory 256m '
                   '--execution-timeout 5s '
                   '--runtime python37 '
                   '--entrypoint index.handler '
                   f'--service-account-id {idAccount} '
                   '--source-path index.py']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    print("Делаем функцию публичной")
    prog_config = ['powershell',
                   'yc serverless function allow-unauthenticated-invoke my-first-function']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    prog_config = ['powershell',
                   'yc serverless function get my-first-function']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    print(result)

    menu()


def CreateIndex2Py():
    nameObjectStorage = input("Введите имя бакета: ")
    prog_config = ['powershell',
                   'yc iam access-key create --service-account-name service-account-for-cf --description "index key practic 3" --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    keyId = str(*re.findall('(key_id: [0-9a-zA-Z_-]*)', result)).replace('key_id: ', '')
    secret = str(*re.findall('(secret: [0-9a-zA-Z_-]*)', result)).replace('secret: ', '')
    print(keyId)
    print(secret)

    text = ('''import os
import datetime
import boto3
import pytz

ACCESS_KEY = "%s"
SECRET_KEY = "%s"
BUCKET_NAME = "%s"
TIME_ZONE = "Europe/Moscow"

TEMP_FILENAME = "/tmp/temp_file"
TEXT_FOR_TEMP_FILE = "This is text file"

def write_temp_file():
    temp_file = open(TEMP_FILENAME, 'w')
    temp_file.write(TEXT_FOR_TEMP_FILE)
    temp_file.close()
    print("\\U0001f680 Temp file is written")

def get_now_datetime_str():
    now = datetime.datetime.now(pytz.timezone(TIME_ZONE))    
    return now.strftime('%%Y-%%m-%%d__%%H-%%M-%%S')

def get_s3_instance():
    session = boto3.session.Session()
    return session.client(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )

def upload_dump_to_s3():
    print("\\U0001F4C2 Starting upload to Object Storage")
    get_s3_instance().upload_file(
        Filename=TEMP_FILENAME,
        Bucket=BUCKET_NAME,
        Key=f'file-{get_now_datetime_str()}.txt'
    )
    print("\\U0001f680 Uploaded")


def remove_temp_files():
    os.remove(TEMP_FILENAME)
    print("\\U0001F44D That's all!")

def handler(event, context):
    write_temp_file()
    upload_dump_to_s3()
    remove_temp_files()
    return {
        'statusCode': 200,
        'body': 'File is uploaded',
    }''') % (keyId, secret, nameObjectStorage)


    file = open('index.py', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')
    input("ЗАГРУЗИ index.py В АРХИВ my-first-function.zip")

    prog_config = ['powershell', 'yc iam service-account get --name service-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)

    prog_config = ['powershell',
                   'yc serverless function version create '
                   '--function-name my-first-function '
                   '--memory 256m '
                   '--execution-timeout 5s '
                   '--runtime python37 '
                   '--entrypoint index.handler '
                   f'--service-account-id {idAccount} '
                   '--source-path my-first-function.zip']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    print("Сохранение ID версии функции")
    prog_config = ['powershell',
                   'yc serverless function version list --function-name my-first-function --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFunction = re.findall('- id: \w*', result)[0].replace('- id: ', '')
    print("Идентификатор версии функции:", idFunction)

    prog_config = ['powershell', 'yc serverless function version create'
                                 ' --function-name my-first-function'
                                 ' --memory 256m'
                                 ' --execution-timeout 5s'
                                 ' --runtime python37'
                                 ' --entrypoint index.handler'
                                 f' --service-account-id {idAccount}'
                                 f' --source-version-id {idFunction}'
                                 f' --environment ACCESS_KEY={keyId}'
                                 f' --environment SECRET_KEY={secret}'
                                 f' --environment BUCKET_NAME={nameObjectStorage}']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    prog_config = ['powershell',
                   'yc serverless function get my-first-function']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    print(result)

    text = ('''def handler(event, context):
    print("\\U0001F4C2 Starting function after trigger")
    print(event)     
    return {
        'statusCode': 200,
        'body': 'File is uploaded',
    }''')

    file = open('index.py', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')
    print("Создание функции триггера")
    prog_config = ['powershell',
                   'yc serverless function create --name my-trigger-function']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    print("Создание версии функции триггера")
    prog_config = ['powershell',
                   'yc serverless function version create'
                   ' --function-name my-trigger-function'
                   ' --memory 256m'
                   ' --execution-timeout 5s'
                   ' --runtime python37'
                   ' --entrypoint index.handler'
                   f' --service-account-id {idAccount}'
                   ' --source-path index.py'
                   ]
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    print("Создание триггера")
    prog_config = ['powershell',
                   'yc serverless trigger create object-storage'
                   ' --name my-first-trigger'
                   f' --bucket-id {nameObjectStorage}'
                   ' --events \'create-object\''
                   ' --invoke-function-name my-trigger-function'
                   f' --invoke-function-service-account-id {idAccount}'
                   ]
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    print("Получение ссылки на функцию")
    prog_config = ['powershell',
                   'yc serverless function get my-first-function']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    print(result)

    menu()


def CreateParrotPy():
    nameObjectStorage = input("Введите имя бакета: ")
    prog_config = ['powershell',
                   'yc iam access-key create --service-account-name service-account-for-cf --description "Parrot key" --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    keyId = str(*re.findall('(key_id: [0-9a-zA-Z_-]*)', result)).replace('key_id: ', '')
    secret = str(*re.findall('(secret: [0-9a-zA-Z_-]*)', result)).replace('secret: ', '')
    print("ID ключа:",keyId)
    print("Секретная часть ключа:",secret)

    prog_config = ['powershell', 'yc iam service-account get --name service-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)

    print("Создание функции")
    prog_config = ['powershell',
                   'yc serverless function create --name  parrot --description "function for Alice"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()


    text = ('''import os
import datetime
import boto3
import pytz

ACCESS_KEY = "%s"
SECRET_KEY = "%s"
BUCKET_NAME = "%s"
TIME_ZONE = "Europe/Moscow"

TEMP_FILENAME = "/tmp/temp_file"
TEXT_FOR_TEMP_FILE = "This is text file"

def write_temp_file(text_for_s3):
    TEXT_FOR_TEMP_FILE = text_for_s3
    temp_file = open(TEMP_FILENAME, 'w')    
    temp_file.write(TEXT_FOR_TEMP_FILE)
    temp_file.close()
    print("\\U0001f680 Temp file is written")

def get_now_datetime_str():
    now = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    return now.strftime('%%Y-%%m-%%d__%%H-%%M-%%S')

def get_s3_instance():
    session = boto3.session.Session()
    return session.client(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )

def upload_dump_to_s3():
    print("\\U0001F4C2 Starting upload to Object Storage")
    get_s3_instance().upload_file(
        Filename=TEMP_FILENAME,
        Bucket=BUCKET_NAME,
        Key=f'file-{get_now_datetime_str()}.txt'
    )
    print("\\U0001f680 Uploaded")


def remove_temp_files():
    os.remove(TEMP_FILENAME)
    print("\\U0001F44D That's all!")

def handler(event, context):
    """
    Entry-point for Serverless Function.
    :param event: request payload.
    :param context: information about current execution context.
    :return: response to be serialized as JSON.
    """
    text = 'Hello! I\\'ll repeat anything you say to me.'
    if 'request' in event and \\
            'original_utterance' in event['request'] \\
            and len(event['request']['original_utterance']) > 0:
        text = event['request']['original_utterance']
        write_temp_file(text)
        upload_dump_to_s3()
        remove_temp_files()
    return {
        'version': event['version'],
        'session': event['session'],
        'response': {
            # Respond with the original request or welcome the user if this is the beginning of the dialog and the request has not yet been made.
            'text': text,
            # Don't finish the session after this response.
            'end_session': 'false'
        },
    }
''') % (keyId, secret, nameObjectStorage)

    file = open('parrot.py', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    input("ЗАКИНЬ parrot.py В АРХИВ parrot.zip")
    prog_config = ['powershell',
                   'yc serverless function version create'
                   ' --function-name=parrot'
                   ' --memory=256m'
                   ' --execution-timeout=5s'
                   ' --runtime=python37'
                   ' --entrypoint=parrot.handler'
                   f' --service-account-id {idAccount}'
                   ' --source-path parrot.zip'
                   ]
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    print("Сохранение ID версии функции")
    prog_config = ['powershell',
                   'yc serverless function version list --function-name parrot --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFunction = re.findall('- id: \w*', result)[0].replace('- id: ', '')
    print("Идентификатор версии функции:", idFunction)

    prog_config = ['powershell', 'yc serverless function version create'
                                 ' --function-name parrot'
                                 ' --memory 256m'
                                 ' --execution-timeout 5s'
                                 ' --runtime python37'
                                 ' --entrypoint parrot.handler'
                                 f' --service-account-id {idAccount}'
                                 f' --source-version-id {idFunction}'
                                 f' --environment ACCESS_KEY={keyId}'
                                 f' --environment SECRET_KEY={secret}'
                                 f' --environment BUCKET_NAME={nameObjectStorage}']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    menu()


def CreatePostgree():
    prog_config = ['powershell', 'yc vpc subnet list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0])
    temp = re.findall('- id: \w*|zone_id: \w*-\w*-\w*', result)
    index = temp.index('zone_id: ru-central1-c')
    idSubnet = str(temp[index - 1]).replace('- id: ', '')
    print('Идентификатор подсети:', idSubnet)

    if input('Создать кластер? д/н') == 'д':
        prog_config = ['powershell',
                       'yc managed-postgresql cluster create'
                       ' --name my-pg-database'
                       ' --description \'For Serverless\''
                       ' --postgresql-version 13'
                       ' --environment production'
                       ' --network-name default'
                       ' --resource-preset b2.nano'
                       f' --host zone-id=ru-central1-c,subnet-id={idSubnet}'
                       ' --disk-type network-hdd'
                       ' --disk-size 10'
                       ' --user name=user1,password=user1user1'
                       ' --database name=db1,owner=user1'
                       ' --websql-access'
                       ' --serverless-access'
                       ]
        subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait()
    input("ЗАГРУЗИ SQL-ЗАПРОС В КЛАССТЕР (В NOTION) И СОЗДАЙ ПОДКЛЮЧЕНИЕ К БД В ОБЛАЧНЫХ ФУНКЦИЯХ")
    connectionId, dbHost = input("Введите идентификатор подключения и точку входа через пробел ").split(" ")

    text = ('''import datetime
import logging
import requests
import os

#Эти библиотеки нужны для работы с PostgreSQL
import psycopg2
import psycopg2.errors

CONNECTION_ID = "%s"
DB_USER = "user1"
DB_HOST = "%s"

# Настраиваем функцию для записи информации в журнал функции
# Получаем стандартный логер языка Python
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Вычитываем переменную VERBOSE_LOG, которую мы указываем в переменных окружения
verboseLogging = eval(os.environ['VERBOSE_LOG'])  ## Convert to bool

#Функция log, которая запишет текст в журнал выполнения функции, если в переменной окружения VERBOSE_LOG будет значение True
def log(logString):
    if verboseLogging:
        logger.info(logString)

#Запись в базу данных
def save(result, time, context):
    connection = psycopg2.connect(
        database=CONNECTION_ID, # Идентификатор подключения
        user=DB_USER, # Пользователь БД
        password=context.token["access_token"],
        host=DB_HOST, # Точка входа
        port=6432,
        sslmode="require")

    cursor = connection.cursor()
    postgres_insert_query = """INSERT INTO measurements (result, time) VALUES (%%s,%%s)"""
    record_to_insert = (result, time)
    cursor.execute(postgres_insert_query, record_to_insert)
    connection.commit()

# Это обработчик. Он будет вызван первым при запуске функции
def entry(event, context):

    #Выводим в журнал значения входных параметров event и context
    log(event)
    log(context)

    # Тут мы запоминаем текущее время, отправляем запрос к yandex.ru и вычисляем время выполнения запроса
    try:
        now = datetime.datetime.now()
        #здесь указано два таймаута: 1c для установки связи с сервисом и 3 секунды на получение ответа
        response = requests.get('https://yandex.ru', timeout=(1.0000, 3.0000))
        timediff = datetime.datetime.now() - now
        #сохраняем результат запроса
        result = response.status_code
    #если в процессе запроса сработали таймауты, то в результат записываем соответствующие коды
    except requests.exceptions.ReadTimeout:
        result = 601
    except requests.exceptions.ConnectTimeout:
        result = 602
    except requests.exceptions.Timeout:
        result = 603
    log(f'Result: {result} Time: {timediff.total_seconds()}')
    save(result, timediff.total_seconds(), context)

    #возвращаем результат запроса
    return {
        'statusCode': result,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'isBase64Encoded': False
    }''') % (connectionId, dbHost)

    file = open('function-for-postgresql.py', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    prog_config = ['powershell',
                   'yc serverless function create'
                   ' --name  function-for-postgresql'
                   ' --description \"function for postgresql\"'
                   ]
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait())
    print('Успешно создана функция')

    prog_config = ['powershell', 'yc iam service-account get --name service-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)
    prog_config = ['powershell',
                   'yc serverless function version create'
                   ' --function-name=function-for-postgresql'
                   ' --memory=256m'
                   ' --execution-timeout=5s'
                   ' --runtime=python37'
                   ' --entrypoint=function-for-postgresql.entry'
                   f' --service-account-id {idAccount}'
                   ' --environment VERBOSE_LOG=True'
                   f' --environment CONNECTION_ID={connectionId}'
                   ' --environment DB_USER=user1'
                   f' --environment DB_HOST={dbHost}'
                   ' --source-path function-for-postgresql.py'
                   ]
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait())


    prog_config = ['powershell',
                   'yc serverless trigger create timer'
                   ' --name trigger-for-postgresql'
                   ' --invoke-function-name function-for-postgresql'
                   f' --invoke-function-service-account-id {idAccount}'
                   ' --cron-expression \'* * * * ? *\''
                   ]
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait())
    input("УДАЛИТЬ ТРИГГЕР???")
    prog_config = ['powershell', 'yc serverless trigger delete trigger-for-postgresql']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    menu()


def CreateGateway():
    print('Создание первой спецификации')
    text = ('''openapi: "3.0.0"
info:
  version: 1.0.0
  title: Test API
paths:
  /hello:
    get:
      summary: Say hello
      operationId: hello
      parameters:
        - name: user
          in: query
          description: User name to appear in greetings
          required: false
          schema:
            type: string
            default: 'world'
      responses:
        '200':
          description: Greeting
          content:
            'text/plain':
              schema:
                type: "string"
      x-yc-apigateway-integration:
        type: dummy
        http_code: 200
        http_headers:
          'Content-Type': "text/plain"
        content:
          'text/plain': "Hello, {user}!\\n"''')

    file = open('hello-world.yaml', "w+")
    file.write(text)
    file.close()
    print('Файл hello-world.yaml успешно перезаписан')

    prog_config = ['powershell',
                   'yc serverless api-gateway create --name hello-world --spec=hello-world.yaml --description "hello world"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait()
    print("Успешная загрузка спецификации")

    prog_config = ['powershell',
                   'yc serverless api-gateway get --name hello-world']
    print(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    input("КОПИРУЙ ДОМЕН ВЫШЕ И ЗАПИШИ В NOTION")

    connectionId, dbHost = input("Введите идентификатор подключения и точку входа через пробел ").split(" ")

    text = ('''import json
import logging
import requests
import os

#Эти библиотеки нужны для работы с PostgreSQL
import psycopg2
import psycopg2.errors
import psycopg2.extras

CONNECTION_ID = "%s"
DB_USER = "user1"
DB_HOST = "%s"

# Настраиваем функцию для записи информации в журнал функции
# Получаем стандартный логер языка Python
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Вычитываем переменную VERBOSE_LOG, которую мы указываем в переменных окружения
verboseLogging = eval(os.environ['VERBOSE_LOG'])  ## Convert to bool

#Функция log, которая запишет текст в журнал выполнения функции, если в переменной окружения VERBOSE_LOG будет значение True
def log(logString):
    if verboseLogging:
        logger.info(logString)

#Запись в базу данных
def save(result, time, context):
    connection = psycopg2.connect(
        database=CONNECTION_ID, # Идентификатор подключения
        user=DB_USER, # Пользователь БД
        password=context.token["access_token"],
        host=DB_HOST, # Точка входа
        port=6432,
        sslmode="require")

    cursor = connection.cursor()
    postgres_insert_query = """INSERT INTO measurements (result, time) VALUES (%%s,%%s)"""
    record_to_insert = (result, time)
    cursor.execute(postgres_insert_query, record_to_insert)
    connection.commit()

#Формируем запрос
def generateQuery():
    select = f"SELECT * FROM measurements LIMIT 50"
    result = select
    return result

#Получаем подключение
def getConnString(context):
    """
    Extract env variables to connect to DB and return a db string
    Raise an error if the env variables are not set
    :return: string
    """
    connection = psycopg2.connect(
        database=CONNECTION_ID, # Идентификатор подключения
        user=DB_USER, # Пользователь БД
        password=context.token["access_token"],
        host=DB_HOST, # Точка входа
        port=6432,
        sslmode="require")
    return connection

def handler(event, context):
    try:
        secret = event['queryStringParameters']['secret']
        if secret != 'cecfb23c-bc86-4ca2-b611-e79bc77e5c31':
            raise Exception()
    except Exception as error:
        logger.error(error)
        statusCode = 401
        return {
            'statusCode': statusCode
        }

    sql = generateQuery()
    log(f'Exec: {sql}')

    connection = getConnString(context)
    log(f'Connecting: {connection}')
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
        statusCode = 200
        return {
            'statusCode': statusCode,
            'body': json.dumps(cursor.fetchall()),
        }
    except psycopg2.errors.UndefinedTable as error:
        connection.rollback()
        logger.error(error)
        statusCode = 500
    except Exception as error:
        logger.error(error)
        statusCode = 500
    cursor.close()
    connection.close()

    return {
        'statusCode': statusCode,
        'body': json.dumps({
            'event': event,
        }),
    }
''') % (connectionId, dbHost)


    file = open('function-for-user-requests.py', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    print('Создание функции')
    prog_config = ['powershell',
                   'yc serverless function create '
                   '--name  function-for-user-requests '
                   '--description \"function for respons to user\"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait()
    print('Функция успешно создана')

    print('Получение ID аккаунта')
    prog_config = ['powershell', 'yc iam service-account get --name service-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)

    print("Создание версии функции function-for-user-requests")
    prog_config = ['powershell',
                   'yc serverless function version create'
                   ' --function-name=function-for-user-requests'
                   ' --memory=256m'
                   ' --execution-timeout=5s'
                   ' --runtime=python37'
                   ' --entrypoint=function-for-user-requests.handler'
                   f' --service-account-id {idAccount}'
                   ' --environment VERBOSE_LOG=True'
                   f' --environment CONNECTION_ID={connectionId}'
                   ' --environment DB_USER=user1'
                   f' --environment DB_HOST={dbHost}'
                   ' --source-path function-for-user-requests.py'
                   ]
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    print("Успешно")

    print("Сохранение ID функции")
    prog_config = ['powershell',
                   'yc serverless function version list --function-name function-for-user-requests --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFunction = re.findall('function_id: \w*', result)[0].replace('function_id: ', '')
    print("Идентификатор функции:", idFunction)

    text = ('''openapi: "3.0.0"
info:
  version: 1.0.0
  title: Updated API
paths:
  /results:
    get:
      x-yc-apigateway-integration:
        type: cloud-functions
        function_id: %s
        service_account_id: %s
      operationId: function-for-user-requests''') % (idFunction, idAccount)

    file = open('hello-world.yaml', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    prog_config = ['powershell', 'yc serverless api-gateway update --name hello-world --spec=hello-world.yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait())
    print("Успешная перезагрузка")

    menu()


def CreateSeriesScripts():
    print("Получение DocAPI")
    prog_config = ['powershell', 'yc ydb database list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    DocAPI = re.findall('(https?://[\w.-]+/[\w.-]+/[\w.-]+/[\w.-]+)', result)[0]
    print(DocAPI)
    text = ('''import boto3

def create_series_table():
    ydb_docapi_client = boto3.resource('dynamodb', endpoint_url = "%s")

    table = ydb_docapi_client.create_table(
        TableName = 'docapitest/series', # Series — имя таблицы
        KeySchema = [
            {
                'AttributeName': 'series_id',
                'KeyType': 'HASH'  # Ключ партицирования
            },
            {
                'AttributeName': 'title',
                'KeyType': 'RANGE'  # Ключ сортировки
            }
        ],
        AttributeDefinitions = [
            {
                'AttributeName': 'series_id',
                'AttributeType': 'N'  # Целое число
            },
            {
                'AttributeName': 'title',
                'AttributeType': 'S'  # Строка
            },

        ]
    )
    return table

if __name__ == '__main__':
    series_table = create_series_table()
    print("Статус таблицы:", series_table.table_status)''') % (DocAPI)

    file = open('SeriesCreateTable.py', "w+", encoding="utf-8")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    text = ('''from decimal import Decimal
import json
import boto3

def load_series(series):
    ydb_docapi_client = boto3.resource('dynamodb', endpoint_url = "%s")

    table = ydb_docapi_client.Table('docapitest/series')
    for serie in series:
        series_id = int(serie['series_id'])
        title = serie['title']
        print("Добавлен сериал:", series_id, title)
        table.put_item(Item = serie)

if __name__ == '__main__':
    with open("seriesdata.json") as json_file:
        serie_list = json.load(json_file, parse_float = Decimal)
    load_series(serie_list)''') % (DocAPI)

    file = open('SeriesLoadData.py', "w+", encoding="utf-8")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    menu()


def CreateScripts():
    prog_config = ['powershell',
                   'yc iam access-key create --service-account-name service-account-for-cf --description "index key practic 9" --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    keyId = str(*re.findall('(key_id: [0-9a-zA-Z_-]*)', result)).replace('key_id: ', '')
    secret = str(*re.findall('(secret: [0-9a-zA-Z_-]*)', result)).replace('secret: ', '')
    print(keyId)
    print(secret)

    queueUrl = input("Создайте очередь и введите адресс очереди: ")

    text = ('''import logging
import os
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

verboseLogging = eval("True")  ## Convert to bool
queue_url = "%s"

def log(logString):
    if verboseLogging:
        logger.info(logString)

def handler(event, context):

    # Get url
    try:
        url = event['queryStringParameters']['url']
    except Exception as error:
        logger.error(error)
        statusCode = 400
        return {
            'statusCode': statusCode
        }

    # Create client
    client = boto3.client(
        service_name='sqs',
        endpoint_url='https://message-queue.api.cloud.yandex.net',
        region_name='ru-central1'
    )

    # Send message to queue
    client.send_message(
        QueueUrl=queue_url,
        MessageBody=url
    )
    log('Successfully sent test message to queue')

    statusCode = 200

    return {
        'statusCode': statusCode
    }''') % (queueUrl)

    file = open('my-url-receiver-function.py', "w+", encoding="utf-8")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    print("Создание функции")
    prog_config = ['powershell',
                   'yc serverless function create --name  my-url-receiver-function --description "function for url"']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    print('Получение ID аккаунта')
    prog_config = ['powershell', 'yc iam service-account get --name service-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)

    input("АРХИВИРУЙ 2 ФАЙЛА В my-url-receiver-function.zip")

    print("Изменение функции")
    prog_config = ['powershell',
                   'yc serverless function version create '
                   '--function-name=my-url-receiver-function '
                   '--memory=256m '
                   '--execution-timeout=5s '
                   '--runtime=python37 '
                   '--entrypoint=my-url-receiver-function.handler '
                   '--service-account-id %s  '
                   '--environment VERBOSE_LOG=True '
                   '--environment AWS_ACCESS_KEY_ID=%s '
                   '--environment AWS_SECRET_ACCESS_KEY=%s '
                   '--environment QUEUE_URL=%s '
                   '--source-path my-url-receiver-function.zip' % (idAccount, keyId, secret, queueUrl)]
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    print("Сохранение ID функции")
    prog_config = ['powershell',
                   'yc serverless function version list --function-name my-url-receiver-function --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFunction = re.findall('function_id: \w*', result)[0].replace('function_id: ', '')
    print("Идентификатор функции:", idFunction)

    print('Создание первой спецификации')
    text = ('''openapi: "3.0.0"
info:
  version: 1.0.0
  title: Test API
paths:
  /check:
    get:
        x-yc-apigateway-integration:
            type: cloud-functions
            function_id: %s
            service_account_id: %s
        operationId: add-url''' % (idFunction, idAccount))

    file = open('hello-world.yaml', "w+")
    file.write(text)
    file.close()
    print('+++Файл hello-world.yaml успешно перезаписан+++')

    prog_config = ['powershell', 'yc serverless api-gateway update --name hello-world --spec=hello-world.yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait())
    print("Успешная перезагрузка")

    connectionId, dbHost = input("Введите идентификатор подключения и точку входа через пробел ").split(" ")

    text = ('''import logging
import os
import boto3
import datetime
import requests

#Эти библиотеки нужны для работы с PostgreSQL
import psycopg2
import psycopg2.errors
import psycopg2.extras

CONNECTION_ID = "%s"
DB_USER = "user1"
DB_HOST = "%s"
QUEUE_URL = "%s"

# Настраиваем функцию для записи информации в журнал функции
# Получаем стандартный логер языка Python
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Вычитываем переменную VERBOSE_LOG, которую мы указываем в переменных окружения 
verboseLogging = eval("True")  ## Convert to bool

#Функция log, которая запишет текст в журнал выполнения функции, если в переменной окружения VERBOSE_LOG будет значение True
def log(logString):
    if verboseLogging:
        logger.info(logString)

#Получаем подключение
def getConnString(context):
    """
    Extract env variables to connect to DB and return a db string
    Raise an error if the env variables are not set
    :return: string
    """
    connection = psycopg2.connect(
        database=CONNECTION_ID, # Идентификатор подключения
        user=DB_USER, # Пользователь БД
        password=context.token["access_token"],
        host=DB_HOST, # Точка входа
        port=6432,
        sslmode="require")
    return connection

"""
    Create SQL query with table creation
"""
def makeCreateDataTableQuery(table_name):
    query = f"""CREATE TABLE public.{table_name} (
    url text,
    result integer,
    time float
    )"""
    return query

def makeInsertDataQuery(table_name, url, result, time):
    query = f"""INSERT INTO {table_name} 
    (url, result,time)
    VALUES('{url}', {result}, {time})
    """
    return query

def handler(event, context):

    # Create client
    client = boto3.client(
        service_name='sqs',
        endpoint_url='https://message-queue.api.cloud.yandex.net',
        region_name='ru-central1'
    )

    # Receive sent message
    messages = client.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        VisibilityTimeout=60,
        WaitTimeSeconds=1
    ).get('Messages')

    if messages is None:
        return {
            'statusCode': 200
        }

    for msg in messages:
        log('Received message: "{}"'.format(msg.get('Body')))

    # Get url from message
    url = msg.get('Body');

    # Check url
    try:
        now = datetime.datetime.now()
        response = requests.get(url, timeout=(1.0000, 3.0000))
        timediff = datetime.datetime.now() - now
        result = response.status_code
    except requests.exceptions.ReadTimeout:
        result = 601
    except requests.exceptions.ConnectTimeout:
        result = 602
    except requests.exceptions.Timeout:
        result = 603
    log(f'Result: {result} Time: {timediff.total_seconds()}')
    
    connection = getConnString(context)
    log(f'Connecting: {connection}')    
    cursor = connection.cursor()

    table_name = 'custom_request_result'
    sql = makeInsertDataQuery(table_name, url, result, timediff.total_seconds())

    log(f'Exec: {sql}')
    try:
        cursor.execute(sql)
    except psycopg2.errors.UndefinedTable as error:
        log(f'Table not exist - create and repeate insert')
        connection.rollback()
        logger.error(error)
        createTable = makeCreateDataTableQuery(table_name)
        log(f'Exec: {createTable}')
        cursor.execute(createTable)
        connection.commit()
        log(f'Exec: {sql}')
        cursor.execute(sql)
    except Exception as error:
        logger.error( error)

    connection.commit()
    cursor.close()
    connection.close()

    # Delete processed messages
    for msg in messages:
        client.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=msg.get('ReceiptHandle')
        )
        print('Successfully deleted message by receipt handle "{}"'.format(msg.get('ReceiptHandle')))

    statusCode = 200

    return {
        'statusCode': statusCode
    }''') % (connectionId, dbHost, queueUrl)

    file = open('function-for-url-from-mq.py', "w+", encoding="utf-8")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    print("Создание функции")
    prog_config = ['powershell',
                   'yc serverless function create --name  function-for-url-from-mq --description "function for url from mq"']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    input("ДОБАВЬ ФАЙЛ В function-for-url-from-mq.zip")

    print("Изменение функции")
    prog_config = ['powershell',
                   'yc serverless function version create '
                   '--function-name=function-for-url-from-mq '
                   '--memory=256m '
                   '--execution-timeout=5s '
                   '--runtime=python37 '
                   '--entrypoint=function-for-url-from-mq.handler '
                   '--service-account-id %s  '
                   '--environment VERBOSE_LOG=True '
                   '--environment CONNECTION_ID=%s '
                   '--environment DB_USER=user1 '
                   '--environment DB_HOST=%s '
                   '--environment AWS_ACCESS_KEY_ID=%s '
                   '--environment AWS_SECRET_ACCESS_KEY=%s '
                   '--environment QUEUE_URL=%s '
                   '--source-path function-for-url-from-mq.zip' % (
                       idAccount, connectionId, dbHost, keyId, secret, queueUrl)]
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    print("Создание функции")
    prog_config = ['powershell',
                   'yc serverless trigger create timer '
                   '--name trigger-for-mq '
                   '--invoke-function-name function-for-url-from-mq '
                   '--invoke-function-service-account-id %s '
                   '--cron-expression \'* * * * ? *\'' % idAccount]
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    input("ПОСЛЕ ВВОДА УДАЛИТСЯ ТРИГГЕР")

    print("Удаление триггера")
    prog_config = ['powershell',
                   'yc serverless trigger delete trigger-for-mq']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    menu()

def Lockbox():
    print("Создание и получение ID сервисного аккаунта")
    prog_config = ['powershell', 'yc iam service-account get --name ffmpeg-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)

    prog_config = ['powershell', 'yc config list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFolder = re.findall('folder-id: \w*', result)[0].replace('folder-id: ', '')
    print("ID Folder ", idFolder)

    prog_config = ['powershell',
                   'yc iam access-key create --service-account-name ffmpeg-account-for-cf --description "index key practic 10" --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    keyId = str(*re.findall('(key_id: [0-9a-zA-Z_-]*)', result)).replace('key_id: ', '')
    secret = str(*re.findall('(secret: [0-9a-zA-Z_-]*)', result)).replace('secret: ', '')
    print(keyId)
    print(secret)

    prog_config = ['powershell',
                   'yc lockbox secret create '
                   '--name ffmpeg-sa-key '
                   f'--folder-id {idFolder} '
                   '--description "keys for serverless" '
                   f'--payload \'[{{"key": "ACCESS_KEY_ID", "text_value": {keyId} }}, {{"key": "SECRET_ACCESS_KEY", "text_value": {secret} }}]\'']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    print("Получение секретного ID LockBox")
    prog_config = ['powershell',
                   'yc lockbox secret get --name ffmpeg-sa-key']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    secretLockbox = re.findall('secret_id: \w*', result)[0].replace('secret_id: ', '')
    print(secretLockbox)
    #
    ymqQueueUrl = input('Введите URL очереди: ')
    ymqQueueArn = input('Введите ARN очереди: ')

    prog_config = ['powershell',
                   f'yc ydb database create ffmpeg --serverless --folder-id {idFolder}']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    prog_config = ['powershell', 'yc ydb database list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    DocAPI = re.findall('(https?://[\w.-]+/[\w.-]+/[\w.-]+/[\w.-]+)', result)[0]
    print("DocumentAPI:", DocAPI)

    input("СОЗДАЙ ТАБЛИЦУ С ПОМОЩЬЮ AWS CLI")
    input("ВЫПОЛНЯЙ ВСЁ ЧТО ТРЕБУЕТСЯ В NOTION И ТОЛЬКО ПОТОМ ПРОДОЛЖАЙ")
    nameBucket = input("Введи имя бакета")
    text = (f'''import json
import os
import subprocess
import uuid
from urllib.parse import urlencode

import boto3
import requests
import yandexcloud
from yandex.cloud.lockbox.v1.payload_service_pb2 import GetPayloadRequest
from yandex.cloud.lockbox.v1.payload_service_pb2_grpc import PayloadServiceStub

boto_session = None
storage_client = None
docapi_table = None
ymq_queue = None


def get_boto_session():
    global boto_session
    if boto_session is not None:
        return boto_session

    # initialize lockbox and read secret value
    yc_sdk = yandexcloud.SDK()
    channel = yc_sdk._channels.channel("lockbox-payload")
    lockbox = PayloadServiceStub(channel)
    response = lockbox.Get(GetPayloadRequest(secret_id='{secretLockbox}'))

    # extract values from secret
    access_key = None
    secret_key = None
    for entry in response.entries:
        if entry.key == 'ACCESS_KEY_ID':
            access_key = entry.text_value
        elif entry.key == 'SECRET_ACCESS_KEY':
            secret_key = entry.text_value
    if access_key is None or secret_key is None:
        raise Exception("secrets required")
    print("Key id: " + access_key)

    # initialize boto session
    boto_session = boto3.session.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    return boto_session


def get_ymq_queue():
    global ymq_queue
    if ymq_queue is not None:
        return ymq_queue

    ymq_queue = get_boto_session().resource(
        service_name='sqs',
        endpoint_url='https://message-queue.api.cloud.yandex.net',
        region_name='ru-central1'
    ).Queue('{ymqQueueUrl}')
    return ymq_queue


def get_docapi_table():
    global docapi_table
    if docapi_table is not None:
        return docapi_table

    docapi_table = get_boto_session().resource(
        'dynamodb',
        endpoint_url='{DocAPI}',
        region_name='ru-central1'
    ).Table('tasks')
    return docapi_table


def get_storage_client():
    global storage_client
    if storage_client is not None:
        return storage_client

    storage_client = get_boto_session().client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        region_name='ru-central1'
    )
    return storage_client

# API handler

def create_task(src_url):
    task_id = str(uuid.uuid4())
    get_docapi_table().put_item(Item={{
        'task_id': task_id,
        'ready': False
    }})
    get_ymq_queue().send_message(MessageBody=json.dumps({{'task_id': task_id, "src": src_url}}))
    return {{
        'task_id': task_id
    }}


def get_task_status(task_id):
    task = get_docapi_table().get_item(Key={{
        "task_id": task_id
    }})
    if task['Item']['ready']:
        return {{
            'ready': True,
            'gif_url': task['Item']['gif_url']
        }}
    return {{'ready': False}}


def handle_api(event, context):
    action = event['action']
    if action == 'convert':
        return create_task(event['src_url'])
    elif action == 'get_task_status':
        return get_task_status(event['task_id'])
    else:
        return {{"error": "unknown action: " + action}}

# Converter handler

def download_from_ya_disk(public_key, dst):
    api_call_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?' + \\
                   urlencode(dict(public_key=public_key))
    response = requests.get(api_call_url)
    download_url = response.json()['href']
    download_response = requests.get(download_url)
    with open(dst, 'wb') as video_file:
        video_file.write(download_response.content)


def upload_and_presign(file_path, object_name):
    client = get_storage_client()
    bucket = '{nameBucket}'
    client.upload_file(file_path, bucket, object_name)
    return client.generate_presigned_url('get_object', Params={{'Bucket': bucket, 'Key': object_name}}, ExpiresIn=3600)


def handle_process_event(event, context):
    for message in event['messages']:
        task_json = json.loads(message['details']['message']['body'])
        task_id = task_json['task_id']
        # Download video
        download_from_ya_disk(task_json['src'], '/tmp/video.mp4')
        # Convert with ffmpeg
        subprocess.run(['ffmpeg', '-i', '/tmp/video.mp4', '-r', '10', '-s', '320x240', '/tmp/result.gif'])
        result_object = task_id + ".gif"
        # Upload to Object Storage and generate presigned url
        result_download_url = upload_and_presign('/tmp/result.gif', result_object)
        # Update task status in DocAPI
        get_docapi_table().update_item(
            Key={{'task_id': task_id}},
            AttributeUpdates={{
                'ready': {{'Value': True, 'Action': 'PUT'}},
                'gif_url': {{'Value': result_download_url, 'Action': 'PUT'}},
            }}
        )
    return "OK"''')

    if input("Вы уверены что хотите перезаписать файл? (д\н)").lower() == "д":
        file = open('index.py', "w+")
        file.write(text)
        file.close()
        print('Файл успешно перезаписан')
    else:
        print('Файл не перезаписан')

    input("ЗАПИХИВАЙ В АРХИВ И ЗАКИДЫВАЙ ЭТОТ АРХИВ В БАКЕТ")

    print('Создание двух функций')
    prog_config = ['powershell',
                   'yc serverless function create --name ffmpeg-api --description "function for ffmpeg-api"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    prog_config = ['powershell',
                   'yc serverless function create --name ffmpeg-converter --description "function for ffmpeg-converter"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    print('Изменение двух функций')
    prog_config = ['powershell',
                   'yc serverless function version create'
                   ' --function-name ffmpeg-api'
                   ' --memory=256m'
                   ' --execution-timeout=5s'
                   ' --runtime=python37'
                   ' --entrypoint=index.handle_api'
                   f' --service-account-id {idAccount}'
                   f' --environment SECRET_ID={secretLockbox}'
                   f' --environment YMQ_QUEUE_URL={ymqQueueUrl}'
                   f' --environment DOCAPI_ENDPOINT={DocAPI}'
                   f' --environment ACCESS_KEY_ID={keyId}'
                   f' --environment SECRET_ACCESS_KEY={secret}'
                   f' --package-bucket-name {nameBucket}'
                   ' --package-object-name src.zip']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    prog_config = ['powershell',
                   'yc serverless function version create'
                   ' --function-name ffmpeg-converter'
                   ' --memory=2048m'
                   ' --execution-timeout=600s'
                   ' --runtime=python37'
                   ' --entrypoint=index.handle_process_event'
                   f' --service-account-id {idAccount}'
                   f' --environment SECRET_ID={secretLockbox}'
                   f' --environment YMQ_QUEUE_URL={ymqQueueUrl}'
                   f' --environment DOCAPI_ENDPOINT={DocAPI}'
                   f' --environment ACCESS_KEY_ID={keyId}'
                   f' --environment SECRET_ACCESS_KEY={secret}'
                   f' --environment S3_BUCKET={nameBucket}'
                   f' --package-bucket-name {nameBucket}'
                   ' --package-object-name src.zip'
                   ]
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    print('Создание триггера')
    prog_config = ['powershell',
                   'yc serverless trigger create message-queue'
                   '  --name ffmpeg'
                   f'  --queue {ymqQueueArn}'
                   f'  --queue-service-account-id {idAccount}'
                   '  --invoke-function-name ffmpeg-converter '
                   f'  --invoke-function-service-account-id {idAccount}'
                   '  --batch-size 1'
                   '  --batch-cutoff 10s'
                   ]
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    input("УДАЛИТЬ ТРИГГЕР???")

    print('Удаление триггера')
    prog_config = ['powershell', 'yc serverless trigger delete ffmpeg']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()


def CreateFinal():
    prog_config = ['powershell', 'yc config list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFolder = re.findall('folder-id: \w*', result)[0].replace('folder-id: ', '')
    print("ID Folder ", idFolder)

    prog_config = ['powershell',
                   f'yc ydb database create for-serverless-shortener --serverless --folder-id {idFolder}']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    prog_config = ['powershell', 'yc ydb database get --name for-serverless-shortener --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    endpoint = re.findall('endpoint: grpcs?://\w*\.\w*\.\w*\.\w*\:\w*', result)[0].replace('endpoint: ', '')
    database = re.findall('database=/\w*-\w*/\w*/\w*', result)[0].replace('database=', '')
    print("DocumentAPI:", endpoint, database)

    prog_config = ['powershell',
                   'yc iam key create --service-account-name serverless-shortener --output serverless-shortener.sa']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())

    prog_config = ['powershell',
                   f'ydb --endpoint {endpoint} '
                   f'--database {database} '
                   f'--sa-key-file serverless-shortener.sa discovery whoami --groups']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    prog_config = ['powershell',
                   f'ydb --endpoint {endpoint} '
                   f'--database {database} '
                   f'--sa-key-file serverless-shortener.sa scripting yql --file links.yql']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    prog_config = ['powershell',
                   f'ydb --endpoint {endpoint} '
                   f'--database {database} '
                   f'--sa-key-file serverless-shortener.sa scheme describe links']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    text = ('''from kikimr.public.sdk.python import client as ydb

import urllib.parse
import hashlib
import base64
import json
import os


def decode(event, body):
    # тело запроса может быть закодировано
    is_base64_encoded = event.get('isBase64Encoded')
    if is_base64_encoded:
        body = str(base64.b64decode(body), 'utf-8')
    return body


def response(statusCode, headers, isBase64Encoded, body):
    return {
        'statusCode': statusCode,
        'headers': headers,
        'isBase64Encoded': isBase64Encoded,
        'body': body,
    }


def get_config():
    endpoint = os.getenv("endpoint")
    database = os.getenv("database")
    if endpoint is None or database is None:
        raise AssertionError("Нужно указать обе переменные окружения")
    credentials = ydb.construct_credentials_from_environ()
    return ydb.DriverConfig(endpoint, database, credentials=credentials)


def execute(config, query, params):
    with ydb.Driver(config) as driver:
        try:
            driver.wait(timeout=5)
        except TimeoutError:
            print("Connect failed to YDB")
            print("Last reported errors by discovery:")
            print(driver.discovery_debug_details())
            return None

        session = driver.table_client.session().create()
        prepared_query = session.prepare(query)

        return session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query,
            params,
            commit_tx=True
        )


def insert_link(id, link):
    config = get_config()
    query = """
        DECLARE $id AS Utf8;
        DECLARE $link AS Utf8;

        UPSERT INTO links (id, link) VALUES ($id, $link);
        """
    params = {'$id': id, '$link': link}
    execute(config, query, params)


def find_link(id):
    print(id)
    config = get_config()
    query = """
        DECLARE $id AS Utf8;

        SELECT link FROM links where id=$id;
        """
    params = {'$id': id}
    result_set = execute(config, query, params)
    if not result_set or not result_set[0].rows:
        return None

    return result_set[0].rows[0].link


def shorten(event):
    body = event.get('body')

    if body:
        body = decode(event, body)
        original_host = event.get('headers').get('Origin')
        link_id = hashlib.sha256(body.encode('utf8')).hexdigest()[:6]
        # в ссылке могут быть закодированные символы, например, %. это помешает работе api-gateway при редиректе,
        # поэтому следует избавиться от них вызовом urllib.parse.unquote
        insert_link(link_id, urllib.parse.unquote(body))
        return response(200, {'Content-Type': 'application/json'}, False, json.dumps({'url': f'{original_host}/r/{link_id}'}))

    return response(400, {}, False, 'В теле запроса отсутствует параметр url')


def redirect(event):
    link_id = event.get('pathParams').get('id')
    redirect_to = find_link(link_id)

    if redirect_to:
        return response(302, {'Location': redirect_to}, False, '')

    return response(404, {}, False, 'Данной ссылки не существует')


# эти проверки нужны, поскольку функция у нас одна
# в идеале сделать по функции на каждый путь в api-gw
def get_result(url, event):
    if url == "/shorten":
        return shorten(event)
    if url.startswith("/r/"):
        return redirect(event)

    return response(404, {}, False, 'Данного пути не существует')


def handler(event, context):
    url = event.get('url')
    if url:
        # из API-gateway url может прийти со знаком вопроса на конце
        if url[-1] == '?':
            url = url[:-1]
        return get_result(url, event)

    return response(404, {}, False, 'Эту функцию следует вызывать при помощи api-gateway')''')

    file = open('index.py', "w+", encoding="utf-8")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    input("ДОБАВЬ ФАЙЛЫ В АРХИВ SRC")

    prog_config = ['powershell', 'yc iam service-account get --name serverless-shortener']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)

    print("Создание функции")
    prog_config = ['powershell', 'yc serverless function create'
                                 ' --name for-serverless-shortener'
                                 ' --description "function for serverless-shortener"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    print("Добавление версии функции")
    prog_config = ['powershell', 'yc serverless function version create'
                                 ' --function-name for-serverless-shortener'
                                 ' --memory=256m'
                                 ' --execution-timeout=5s'
                                 ' --runtime=python37'
                                 ' --entrypoint=index.handler'
                                 f' --service-account-id {idAccount}'
                                 ' --environment USE_METADATA_CREDENTIALS=1'
                                 ' --environment endpoint=grpcs://ydb.serverless.yandexcloud.net:2135'
                                 f' --environment database={database}'
                                 ' --source-path src.zip']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    print("Открытие функции")
    prog_config = ['powershell', 'yc serverless function allow-unauthenticated-invoke for-serverless-shortener']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    print("Сохранение ID функции")
    prog_config = ['powershell',
                   'yc serverless function version list --function-name for-serverless-shortener --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFunction = re.findall('function_id: \w*', result)[0].replace('function_id: ', '')
    print("Идентификатор функции:", idFunction)

    bucketName = input("Введи имя бакета: ")
    text = (f'''openapi: 3.0.0
info:
  title: for-serverless-shortener
  version: 1.0.0
paths:
  /:
    get:
      x-yc-apigateway-integration:
        type: object_storage
        bucket:             '{bucketName}'
        object:             'index.html'
        presigned_redirect: false
        service_account:    '{idAccount}'
      operationId: static
  /shorten:
    post:
      x-yc-apigateway-integration:
        type: cloud_functions
        function_id:  '{idFunction}'
      operationId: shorten
  /r/{{id}}:
    get:
      x-yc-apigateway-integration:
        type: cloud_functions
        function_id:  '{idFunction}'
      operationId: redirect
      parameters:
        - description: id of the url
          explode: false
          in: path
          name: id
          required: true
          schema:
            type: string
          style: simple''')

    file = open('for-serverless-shortener.yml', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    prog_config = ['powershell', 'yc serverless api-gateway create '
                                 '--name for-serverless-shortener '
                                 '--spec=for-serverless-shortener.yml '
                                 '--description "for serverless shortener"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    prog_config = ['powershell', 'yc serverless api-gateway get --name for-serverless-shortener']
    print(str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()))

    menu()

def CreateServiceAccounts():
    print("Создание и получение ID сервисного аккаунта")
    prog_config = ['powershell',
                   'yc iam service-account create --name ffmpeg-account-for-cf --description "service account for serverless"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    prog_config = ['powershell',
                   'yc iam service-account create --name serverless-shortener --description "service account for serverless"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    prog_config = ['powershell',
                   'yc iam service-account create --name service-account-for-cf --description "service account for cloud functions"']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    prog_config = ['powershell', 'yc config list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFolder = re.findall('folder-id: \w*', result)[0].replace('folder-id: ', '')
    print("ID Folder ", idFolder)

    prog_config = ['powershell', 'yc iam service-account get --name ffmpeg-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount1 = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount1)

    prog_config = ['powershell', 'yc iam service-account get --name serverless-shortener']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount2 = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount2)

    prog_config = ['powershell', 'yc iam service-account get --name service-account-for-cf']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount3 = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount3)

    AddRoleAccount(idFolder, idAccount1, 'storage.viewer')
    AddRoleAccount(idFolder, idAccount1, 'storage.uploader')
    AddRoleAccount(idFolder, idAccount1, 'ymq.reader')
    AddRoleAccount(idFolder, idAccount1, 'ymq.writer')
    AddRoleAccount(idFolder, idAccount1, 'ydb.admin')
    AddRoleAccount(idFolder, idAccount1, 'serverless.functions.invoker')
    AddRoleAccount(idFolder, idAccount1, 'lockbox.payloadViewer')
    AddRoleAccount(idFolder, idAccount1, 'editor')
    AddRoleAccount(idFolder, idAccount2, 'storage.viewer')
    AddRoleAccount(idFolder, idAccount2, 'ydb.admin')
    AddRoleAccount(idFolder, idAccount2, 'editor')
    AddRoleAccount(idFolder, idAccount3, 'editor')
    AddRoleAccount(idFolder, idAccount3, 'storage.editor')
    AddRoleAccount(idFolder, idAccount3, 'serverless.mdbProxies.user')

    menu()

def menu():
    temp = input(
        """Выбери пункт меню
    [1] Инициализация аккаунта (нужно имя и токен)
    [2] Просмотр данных аккаунта, сетей и вм
    [3] Создание первой функции. 2 Практическая
    [4] Создание index.py. 3 Практическая
    [5] Создание parrot.py. 4 Практическая
    [6] Создание кластера Postgree. 5 Практическая
    [7] Создание Gateway. 6 Практическая
    [8] Создание скриптов. 8 Практическая
    [9] Создание скриптов для проверки доступности. 9 Практическая
    [10] Создание файлов для Lockbox
    [11] Создание файлов для Финальной задачи
    [12] Создание всех ролей и сервисных аккаунтов
    Введите число: """)

    if temp == "1":
        name, token = input("Введите имя, токен через пробел: ").split(" ")
        YcInitAccount(name.encode("utf-8"), token.encode("utf-8"))
    elif temp == "2":
        YcList()
    elif temp == "3":
        CreateFirstFunc()
    elif temp == "4":
        CreateIndex2Py()
    elif temp == "5":
        CreateParrotPy()
    elif temp == "6":
        CreatePostgree()
    elif temp == "7":
        CreateGateway()
    elif temp == "8":
        CreateSeriesScripts()
    elif temp == "9":
        CreateScripts()
    elif temp == "10":
        Lockbox()
    elif temp == "11":
        CreateFinal()
    elif temp == "12":
        CreateServiceAccounts()

menu()