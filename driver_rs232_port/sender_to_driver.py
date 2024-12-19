import os
import json
import logging
import requests
import threading

from time import sleep
from dotenv import load_dotenv

from models import Analyzes, delete_analyze, edit_analyze

load_dotenv()
logger = logging.getLogger(__name__)

# буфер открытых портов
opened_ports = []


def send_to_driver(data: bytes, device_number: str, device_name: str, port_parameters: dir):
    """
    Функция посылает результаты анализа проб в LIS

    :param
            force - указание отправить все записи из БД, включая заблокированные
            web - указатель, что запрос на отправку был из ВЕБ-страницы
            semaphore - светофор регулятора доступа к БД
    """
    status = ''
    connection_type = port_parameters.get("d4p1:ConnectionType", '')
    if "USB" in connection_type or "COM" in connection_type:
        # адрес ПРОКСИ сервера
        try:
            url = os.getenv('DRIVER_URL_COM')
        except:
            url = None
            status = f"There is no URL in os.getenv('DRIVER_URL')"
    else:
        # адрес ПРОКСИ сервера
        try:
            url = os.getenv('DRIVER_URL_TCP')
        except:
            url = None
            status = f"There is no URL in os.getenv('DRIVER_URL')"

    if url:
        logger_text = ''
        try:
            logger_text = "Trying to send Data to Analyzer Driver: "
            response = requests.post(
                url=url,
                headers={'Content-type': 'application/json'},
                data=json.dumps({"device_number": device_number,
                                 "device_name": device_name,
                                 "data": data.decode(),
                                 "port_parameters": port_parameters,
                                 }),
                timeout=100,
            )
        except OSError as ex:
            logger_text += "OSError!"
            logger.error(logger_text)
            logger.error(f"Data: \n{data}")
            logger.error(f"OSError is raised: {ex}")
            # status['status'] = f"OSError is raised: {ex.__context__}"
            status = f"OSError is raised: {ex.__context__}"
        except Exception as ex:
            logger_text += "Exception!"
            logger.error(logger_text)
            logger.error(f"Data: \n{data}")
            logger.exception(f"Exception is raised: {ex}")
            status = f"Exception is raised: {ex.__context__}"
        else:
            # если данные приняты прокси сервером
            if response.status_code == 200:
                logger_text += "Success!"
                logger.info(logger_text)
            # если прокси сервер не принял данные
            else:
                logger_text += f"{response.content.decode()}!"
                logger.error(logger_text)
            status = response.status_code
    return status


if __name__ == '__main__':
    # считывания пространства окружения
    load_dotenv()
    # конфигурирование логгера
    logging.basicConfig(level=logging.INFO,
                        # filename='cd_rubylogger.log',
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        )
    logger.info("Start app")
    # send_soap()
    logger.info("Stop app")
