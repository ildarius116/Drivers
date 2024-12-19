import os
import json
import logging
import requests
import platform
import xmltodict
import threading

from typing import List
from datetime import datetime
from flask import Flask, request, render_template
from logging.handlers import RotatingFileHandler

from sender_to_lis import send_soap
from sender_to_driver import send_to_driver as send_to_driver
from models import Analyzes, delete_all_analyzes, delete_analyze_by_id

from drivers.bs_240.transfer_d2d import main as transfer_bs_240
from drivers.bc_30s.transfer_d2d import main as transfer_bc_30s
from drivers.cd_ruby.transfer_d2d import main as transfer_cd_ruby
from drivers.eleven.transfer_d2d import main as transfer_eleven
from drivers.i2000sr.transfer_d2d import main as transfer_i200sr

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


def driver(semaphore: threading, device_number: str, device_name: str, port_parameters: dict):
    app = Flask(__name__)

    @app.errorhandler(404)
    def not_found(e):
        """
        Функция обработки ошибки 404
        """
        # logger.info("NOT FOUND - 404", exc_info=e)
        return f"NOT FOUND - 404 \n {e}"

    @app.route('/', methods=['GET', 'POST'])
    def index():
        """
        Функция обработки данных от драйверов анализатора
        """
        # получение метода полученного запроса
        method = request.method
        results = {}
        # если это метод "POST"
        if method == "POST":
            # получение типа содержимого запроса
            content_type = request.headers.get('Content-Type')
            if content_type == 'application/json':
                # преобразование данных в json формат
                json_data = request.get_json()

                # получение из сообщения названия анализатора
                analyzer_name = json_data.get('analyzer')

                # получение из сообщения номера анализатора
                analyzer_number = json_data.get('device_id')

                # получение из сообщения параметров СОМ порта
                port_parameters = json_data.get('port_parameters')

                # получение из сообщения данных
                data = json_data.get('data')

                if not analyzer_name == "bioway3000":
                    # замена спец символов в строке прямых данных (иначе, вызовет ошибку на стороне ЛИС)
                    char_to_replace = {'&': 'AND', '$': 'DOLLAR', '<': '&lt;', '>': '&gt;'}
                    for key, value in char_to_replace.items():
                        data = data.replace(key, value)

                data = data.encode()

                try:
                    transfer_d2d(semaphore, data, analyzer_name, analyzer_number, port_parameters)
                except Exception as e:
                    return logger.exception(f"Произошла ошибка: {e}")

            # logger.info(f"Send data from proxy driver: {results}")
            return results

        if method == "GET":
            # если это не метод "POST"
            # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
            context = {'title': 'PROXY driver application',
                       'status': 'PROXY driver application is running!',
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

    @app.route("/read_logs")
    def read_logs():
        """
        Функция просмотра файлов логирования
        """
        # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
        context = {'title': 'PROXY driver application',
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
        """
        Функция очистки файла логирования
        """
        # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
        context = {'title': 'PROXY driver application'}
        # открываем ЛОГ-файл в режиме перезаписи
        with open(log_file, 'w') as file:
            # записываем в него пустую строку
            file.write('')
            context['status'] = 'Logfile is cleared'
        return render_template('clear_logs.html', **context)

    @app.route("/read_db")
    def read_database():
        """
        Функция просмотра содержимого Базы Данных
        """
        # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
        context = {'title': 'PROXY driver application',
                   'data_in_db': []}
        # получаем список всех анализов в Базе Данных
        semaphore.acquire()
        all_analyzes = Analyzes.get_all_analyzes()
        semaphore.release()

        for analyze in all_analyzes:
            # вынимаем данные для каждой записи анализов
            row_dict = {"id": analyze.id,
                        "analyzer": analyze.analyzer,
                        "analyzer_id": analyze.device_id,
                        "probe_results": analyze.probe_results,
                        "ready_status": analyze.ready_status,
                        "lines_list": analyze.lines_list,
                        "raw_line": analyze.raw_line,
                        "tries": analyze.tries,
                        "error_text": analyze.error_text,
                        "work_list": analyze.work_list,
                        "buffer": analyze.buffer,
                        }
            # помещаем эти данные в итоговый словарь
            context['data_in_db'].append(row_dict)
        return render_template('read_db.html', **context)

    @app.route("/clear_db")
    def clear_database():
        """
        Функция очистки файла Базы Данных

        param:
            id - id записи в БД
        """
        # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
        context = {'title': 'PROXY driver application'}
        id = None
        # считываем переданный параметр
        for id in request.args.keys():
            # если id передан, то удаляем запись с указанным id
            semaphore.acquire()
            context['status'] = delete_analyze_by_id(id)
            semaphore.release()
        # если id не передан
        if not id:
            # удаляем все записи
            semaphore.acquire()
            context['status'] = delete_all_analyzes()
            semaphore.release()
        return render_template('clear_db.html', **context)

    @app.route("/send_db")
    def send_database():
        """
        Функция отправки данных Базы Данных

        param:
            force - указание отправить все записи из БД, включая заблокированные

        type param:
            force - bool
        """
        # запускаем функцию отправки данных из БД с параметром "усиление"
        status = send_soap(forcibly=True)['status']
        # создаем словарь с переменными контекста и их значениями для вывода на ВЕБ страницу
        context = {'title': 'PROXY driver application',
                   'status': status}
        return render_template('send_db.html', **context)

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

    def transfer_d2d(*args):
        # считываем какую функцию нужно запустить из конфига
        with open("config_transfer.json") as file:
            config = file.read()

        config = json.loads(config)
        function = config.get(analyzer_name)

        if function:
            return globals()[function](*args)
        else:
            logger.exception(f"Неизвестный анализатор {analyzer_name}")

    return app


def get_port_parameters(analyzer_number: str) -> dict:
    """
    Функция запроса параметров COM порта от LIS

    :param
        analyzer_number - номер анализатора

    :return:
        port_parameters - словарь с параметрами порта
    """
    # считывание параметра 'DEBUG' из переменной окружения
    try:
        debug = eval(os.getenv('DEBUG'))
    except Exception as ex:
        debug = False
        logger.exception(f"Exception eval(os.getenv('DEBUG')): \n{ex}")

    # если прописан режим ДЕБАГа
    if debug:
        logger.info(f"DEBUG Mode On: {debug}")
        try:
            # считывание параметра СОМ порта из переменной окружения
            port_parameters = get_from_config(analyzer_number)
            logger.info(f"Got port port_parameters from environment data: {port_parameters}")
            return port_parameters
        except Exception as ex:
            logger.exception(f"Data failure: \n{ex}")
    else:
        # адрес ЛИС сервера
        url = os.getenv('LIS_URL')
        # логин и пароль сервера
        authentication = eval(os.getenv('AUTH'))
        # заголовок сообщения
        headers = {'Content-Type': 'text/xml; charset=utf-8'}
        # СОАП сообщение
        message = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:dev="http://www.medrc.ru/lis/DeviceExchange">
               <soapenv:Header/>
               <soapenv:Body>
                  <dev:GetDeviceSettings>
                     <dev:DeviceID>{analyzer_number}</dev:DeviceID>
                  </dev:GetDeviceSettings>
               </soapenv:Body>
            </soapenv:Envelope>
        """
        # попытка получить параметры COM порта из базы LIS
        try:
            logger.info(f"Trying to send PORT request for id:{analyzer_number}")
            # logger.info(f"Headers: {headers}")
            # logger.info(f"Authentication: {authentication}")
            # logger.info(f"Data: \n{message}")
            response = requests.request("POST", url, headers=headers, data=message, auth=authentication, timeout=5)
        except OSError as ex:
            logger.info(f"Data: \n{message}")
            logger.error(f"OSError is raised: {ex}")
        except Exception as ex:
            logger.info(f"Data: \n{message}")
            logger.error(f"Exception is raised: {ex}")
        else:
            # если связь с базой есть и получены данные
            if response.status_code == 200:
                logger.info(f"status_code: {response.status_code}")
                logger.info(f"PORT port_parameters for id:{analyzer_number} are received")
                logger.info(f"response.text: {response.text}")
                port_parameters_xml = response.text
                port_parameters_dict = xmltodict.parse(port_parameters_xml)
                port_parameters = port_parameters_dict[
                    'soap:Envelope']['soap:Body']['m:GetDeviceSettingsResponse']['m:return']
                return port_parameters
            # если связь с базой есть, но данные не получены
            else:
                logger.info(f"Data: \n{message}")
                logger.info(f"response: {response}")
                logger.warning(f"status_code: {response.status_code}")
                logger.warning(f"PORT port_parameters for id:{analyzer_number} are not received")
                # logger.warning(f"response.text: {response.text}")
                port_parameters = get_from_config(analyzer_number)
                return port_parameters


def get_from_config(analyzer_number: str) -> (dict, str):
    """
    Функция вынимает параметры COM порта из файла "config.json"

    :param
        analyzer_number - номер анализатора

    :return:
        port_parameters - словарь с параметрами COM порта
    """
    config_exists = os.path.exists('config.json')
    if config_exists:
        with open('config.json', 'r') as file:
            content = file.read()
            content = json.loads(content)
            port_parameters = content.get(analyzer_number, {})
            return port_parameters
    return 'File "config.json" is not exists. Reading COM port port_parameters is not able!'


def main(semaphore: threading, analyzer_number: str, analyzer_name: str, port_parameters: dict, host: str, port: int):
    """
    Основная запускающая функция

    :param
        semaphore - регулятор очереди доступа к БД
        analyzer_number - номер анализатора
        analyzer_name - название анализатора
        port_parameters - параметры порта связи драйвера анализатора с анализатором
        host - ip адрес потока прокси драйвера
        port - номер порта потока прокси драйвера
    """

    logger.info("Start app COM-port driver main()")
    driver(semaphore, analyzer_number, analyzer_name, port_parameters).run(debug=True,
                                                                           host=host,
                                                                           port=port,
                                                                           use_reloader=False)


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


if __name__ == '__main__':
    # конфигурирование логгера
    log_file = 'proxy_logger.log'
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%HH:%MM:%SS',
                        force=True,
                        handlers=[RotatingFileHandler(log_file, mode="w", maxBytes=20_000_000, backupCount=10)],
                        # handlers=[TimedRotatingFileHandler(log_file, when="midnight", backupCount=5)],
                        )
    logger = logging.getLogger(__name__)

    # запуск приложения
    logger.info("Start app proxy driver")

    # светофор регулятора очереди доступа к БД
    sem = threading.Semaphore()
    # список будущих потоков
    threads: List[threading.Thread] = []

    # создание потока отправки результатов анализов на прокси сервер для их обработки
    thread = threading.Thread(target=send_soap, kwargs={'semaphore': sem})
    thread.start()
    # успешный запуск помещается в список потоков
    threads.append(thread)

    host = os.getenv('HOST')
    port = os.getenv('PORT')
    if not host:
        host = '0.0.0.0'
    port_text = f"HOST: {host}, "
    if not port:
        port = 5000
    port_text += f"PORT: {port}"
    logger.info(port_text)

    # запуск потоков прокси драйверов, работающих по COM протоколу
    devices = eval(os.getenv('DEVICES_COM'))
    if devices:
        for n, analyzer_number in enumerate(devices):
            logger.info(f"Get port port_parameters from environment data ...")
            port_parameters = get_port_parameters(analyzer_number)
            logger.info(f"Get analyzer_name from environment data ...")
            analyzer_name = port_parameters.get("d4p1:DeviceName")
            port += n
            # отправка параметров СОМ порта на драйвер анализатора
            try:
                logger.info(f"Send ACK to driver ... {analyzer_name} - {analyzer_number}")
                send_to_driver(device_number=analyzer_number,
                               device_name=analyzer_name,
                               data=ACK,
                               port_parameters=port_parameters,
                               )
            except Exception as ex:
                logger.error(f"Exception on send_to_driver analyzer: {analyzer_name} - {analyzer_number}. \nText: {ex}")
            # создание потока получения результатов анализов от анализатора
            try:
                thread = threading.Thread(target=main, kwargs={'semaphore': sem,
                                                               'analyzer_number': analyzer_number,
                                                               'analyzer_name': analyzer_name,
                                                               'port_parameters': port_parameters,
                                                               'host': host,
                                                               'port': port,
                                                               })
                thread.start()
                # успешный запуск помещается в список потоков
                threads.append(thread)
            except Exception as ex:
                logger.error(f"Exception on Thread(target=main): {analyzer_name} - {analyzer_number}. \nText: {ex}")
            port += 1

    # запуск потоков прокси драйверов, работающих по ТСР протоколу
    devices = eval(os.getenv('DEVICES_TCP'))
    if devices:
        for n, analyzer_number in enumerate(devices):
            logger.info(f"Get port port_parameters from environment data ...")
            tcp_parameters = get_port_parameters(analyzer_number)
            logger.info(f"Get analyzer_name from environment data ...")
            analyzer_name = tcp_parameters.get("d4p1:DeviceName")
            port += n
            # отправка параметров TCP порта на драйвер анализатора
            try:
                logger.info(f"Send ACK to driver ... {analyzer_name} - {analyzer_number}")
                send_to_driver(device_number=analyzer_number,
                               device_name=analyzer_name,
                               data=ACK,
                               port_parameters=tcp_parameters,
                               )
            except Exception as ex:
                logger.exception(
                    f"Exception on send_to_driver analyzer: {analyzer_name} - {analyzer_number}. \nText: {ex}")
            # создание потока получения результатов анализов от анализатора
            try:
                thread = threading.Thread(target=main, kwargs={'semaphore': sem,
                                                               'analyzer_number': analyzer_number,
                                                               'analyzer_name': analyzer_name,
                                                               'port_parameters': tcp_parameters,
                                                               'host': host,
                                                               'port': port,
                                                               })
                thread.start()
                # успешный запуск помещается в список потоков
                threads.append(thread)
            except Exception as ex:
                logger.exception(f"Exception on Thread(target=main): {analyzer_name} - {analyzer_number}. \nText: {ex}")

    logger.info("Stop app proxy driver")
