import os
import socket
import logging
import platform
import threading

from typing import List
from datetime import datetime
from flask import Flask, request, render_template
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from sender_to_proxy import send_soap

# буфер открытых портов
open_connections = dict()
# список будущих потоков
threads: List[threading.Thread] = []

app = Flask(__name__)

# стандартные команды
STX = bytes.fromhex("02")
ETX = bytes.fromhex("03")
EOT = bytes.fromhex("04")
ENQ = bytes.fromhex("05")
ACK = bytes.fromhex("06")
LF = bytes.fromhex("0A")
CR = bytes.fromhex("0D")
NAK = bytes.fromhex("15")
ETB = bytes.fromhex("17")


@app.errorhandler(404)
def not_found(e):
    return f"NOT FOUND - 404 \n {e}"


@app.route('/', methods=['GET', 'POST'])
def index():
    # получение метода полученного запроса
    method = request.method
    # если это метод "GET"
    if method == "GET":
        # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
        context = {'title': 'LAN PORT driver application',
                   'status': 'LAN PORT driver application is running!',
                   }
        # открываем ЛОГ-файл в режиме чтения
        with open(log_file, 'r') as file:
            # считываем все строки данных
            content = file.readlines()
            # ограничиваем количество событий для вывода на страницу
            if len(content) > 10:
                content = content[-10:]
            context['last_logs'] = content
        return render_template('index.html', **context)

    # если это метод "POST"
    if method == "POST":
        # получение типа содержимого запроса
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            # преобразование данных в json формат
            json_data = request.get_json()
            # получение номера анализатора
            device_number = json_data.get('device_number')
            # получение наименования анализатора
            device_name = json_data.get('device_name')
            # получение параметров анализатора
            port_parameters = json_data.get('port_parameters')
            # получение данных для анализатора
            data = json_data.get('data')
            # получение ip адреса хоста драйвера анализатора
            host = port_parameters.get('d4p1:host', '')
            # получение номера порта драйвера анализатора
            port = port_parameters.get('d4p1:port', '')
            # получение типа хоста ("сервер" или "клиент") для драйвера анализатора
            host_type = port_parameters.get('d4p1:host_type', '')
            # получение типа кодировки сообщений от анализатора
            encoding_type = port_parameters.get('d4p1:encoding_type', 'utf-8')
            # получение наименования анализатора
            if not device_name:
                device_name = port_parameters.get('d4p1:DeviceName')

            # склеиваем хост и порт для получения ключа
            host_port = host + str(port)
            # проверка открыт ли данный порт
            if host_port in open_connections.keys():
                # проверяем наличие соединения с анализатором и
                # отправляем сообщение от прокси в анализатор
                if open_connections[host_port]:
                    open_connections[host_port].conn.send(data.encode())
                    logger.info(f"Send Data from Proxy to Analyzer №{device_number}: {data}")
                    return f"Send Data from Proxy to Analyzer №{device_number}: {data}"
                else:
                    return f"There is no Serial port opened!"
            else:
                # если порт закрыт - значит добавляем его в словарь открытых и открываем,
                # после обнаружения подключения оно запишется в словарь открытых
                open_connections[host_port] = None
                server = None
                # проверяем тип хоста и создаем соответствующую связь
                if host_type == 'server':
                    server = OpenLanPortServer(host, port, device_number, device_name, port_parameters, encoding_type)
                elif host_type == 'client':
                    server = OpenLanPortClient(host, port, device_number, device_name, port_parameters, encoding_type)
                if server:
                    open_connections[host_port] = server
                    thread = threading.Thread(target=server.listener)
                    thread.start()
                    # успешный запуск помещается в список потоков
                    threads.append(thread)
                    return f"LAN port {host}:{port} is Opened "
                else:
                    return f"LAN port {host}:{port} is not Opened "

        else:
            # если данные в запросе не в json формате
            return 'Only JSON application allowed'


class OpenLanPortServer:
    # класс для хранения информации по одному открытому подключению
    def __init__(self, host, port, number, name, parameters, encoding_type):
        self.host = host
        self.port = port
        self.number = number
        self.name = name
        self.parameters = parameters
        self.encoding_type = encoding_type
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info(f"try to connect: {host}:{port}")
        self.sock.bind((host, port))
        self.sock.listen(5)

        logger.info("ready to connect")
        self.conn, addr = self.sock.accept()

    # метод для включения слушателя
    def listener(self):
        logger.info(f"listener {self.host}:{self.port} is running")
        while True:
            # считывание сообщения от анализатора
            message = self.conn.recv(1024)
            while message:
                logger.info(f"Received Data from Analyzer №{self.number}: {message}")
                # отправка полученных данных
                send_soap(message, self.number, self.name, self.parameters, self.encoding_type)
                # считывание сообщения от анализатора
                message = self.conn.recv(1024)


class OpenLanPortClient:
    # класс для хранения информации по одному открытому подключению
    def __init__(self, host, port, number, name, parameters, encoding_type):
        self.host = host
        self.port = port
        self.number = number
        self.name = name
        self.parameters = parameters
        self.encoding_type = encoding_type
        self.sock = socket.socket()
        logger.info(f"try to connect: {host}:{port}")
        self.sock.connect((host, port))
        logger.info(f"connected to: {host}:{port}")
        self.conn = self.sock

    # метод для включения слушателя
    def listener(self):
        logger.info(f"listener {self.host}:{self.port} is running")
        while True:
            # считывание сообщения от анализатора
            message = self.conn.recv(1024)
            # если это не служебное "пингование"
            if STX not in message:
                logger.info(f"Received Data from Analyzer №{self.number}: {message}")
                # отправка полученных данных
                send_soap(message, self.number, self.name, self.parameters, self.encoding_type)
            # TODO
            #  возможно, не нужно
            self.conn.send(ACK)


@app.route("/read_logs")
def read_logs():
    # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
    context = {'title': 'LAN-port driver application',
               'logs_list': [],
               'old_logs_dict': {},
               'old_log': False,
               }
    # считываем список переданных параметров (лог файла) - список из одного элемента
    old_log_files = request.args.keys()

    # если параметры лог файла переданы
    if old_log_files:
        # получаем название лог файла
        for old_log_file in old_log_files:
            # открываем этот ЛОГ-файл в режиме чтения
            with open(old_log_file, 'r') as file:
                # считываем все строки данных
                content = file.readlines()
                # записываем содержимое лог файла в словарь
                context['logs_list'] = content
                # указатель, что это старый лог файл
                context['old_log'] = True

    # если параметры лог файла НЕ переданы
    else:
        # открываем основной ЛОГ-файл в режиме чтения
        with open(log_file, 'r') as file:
            # считываем все строки данных
            content = file.readlines()
            # записываем содержимое лог файла в словарь
            context['logs_list'] = content
            # указатель, что это новый лог файл
            context['old_log'] = False

        # получаем список всех файлов в текущей папке
        all_files = os.listdir('.')
        # проходимся по списку файлов
        for file in all_files:
            # если это лог файл из ротации (содержит текст "logger.log."
            if 'logger.log.' in file:
                # получаем дату изменения файла
                mod_date = get_file_date(file, False)
                # преобразуем дату в человекочитаемый формат
                mod_date = datetime.fromtimestamp(mod_date).strftime('%Y-%m-%d %H:%M:%S')
                # создаем/обновляем словарь старых лог файлов
                context['old_logs_dict'][file] = mod_date
    return render_template('read_logs.html', **context)


@app.route("/clear_logs")
def clear_logs():
    # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
    context = {'title': 'LAN-port driver application',
               'status': 'LAN-port driver application is running!',
               }
    # открываем ЛОГ-файл в режиме перезаписи
    with open(log_file, 'w') as file:
        # записываем в него пустую строку
        file.write('')
        context['status'] = 'Logfile is cleared'
    return render_template('clear_logs.html', **context)


def get_file_date(path_to_file: str, creation_date: bool = True) -> float:
    """
    Функция получения времени создания и модификации файла

    :param
        path_to_file - путь до файла
        creation_date - указатель, что надо получить время создания

    :return:
        Время создания и/или модификации файла
    """
    # считываем название платформы (ОС)
    # если это "Windows"
    if platform.system() == 'Windows':
        # если передан параметр получения даты создания файла
        if creation_date:
            # передаем время создания файла
            return os.path.getctime(path_to_file)
        # если НЕ передан параметр получения даты создания файла
        # передаем время изменения файла
        return os.path.getmtime(path_to_file)

    # если платформа НЕ "Windows"
    else:
        # считываем статистические данные файла
        stat = os.stat(path_to_file)
        # пытаемся обработать эти данные
        try:
            # если передан параметр получения даты создания файла
            if creation_date:
                # передаем время создания файла
                return stat.st_birthtime
            # если НЕ передан параметр получения даты создания файла
            # передаем время изменения файла
            return stat.st_mtime
        except AttributeError:
            # в Linux системе, бывает невозможно получить дату создания файла
            # в этом случае, передаем время изменения файла
            return stat.st_mtime


# Запуск приложения
if __name__ == '__main__':
    # конфигурирование логгера
    log_file = 'driver_logger.log'
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%HH:%MM:%SS',
                        force=True,
                        handlers=[RotatingFileHandler(log_file, mode="w", maxBytes=10_000_000, backupCount=10)],
                        # handlers=[TimedRotatingFileHandler(log_file, when="midnight", backupCount=5)],
                        )
    logger = logging.getLogger(__name__)

    # запуск приложения
    logger.info("Start app LAN-port driver")
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    if not host:
        host = '0.0.0.0'
    port_text = f"HOST: {host}, "
    if not port:
        port = 5050
    port_text += f"PORT: {port}"
    logger.info(port_text)
    try:
        app.run(debug=True, host=host, port=port, use_reloader=False)
    except Exception as ex:
        logger.exception(f"Exception on {port_text}. Text: {ex}")
    logger.info("Stop app LAN-port driver")
