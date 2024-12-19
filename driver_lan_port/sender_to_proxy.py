import os
import json
import logging
import requests

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# буфер открытых портов
opened_ports = []


def send_soap(data: bytes = b'',
              device_number: str = "",
              device_name: str = "",
              port_parameters: dir = None,
              encoding_type: str = "utf-8",
              ) -> None:
    """
    Функция посылает результаты анализа проб в LIS

    :param
            force - указание отправить все записи из БД, включая заблокированные
            web - указатель, что запрос на отправку был из ВЕБ-страницы
            semaphore - светофор регулятора доступа к БД
    """
    # адрес ПРОКСИ сервера
    url = os.getenv('PROXY_URL')
    status = {'status': ''}
    logger_text = ''
    try:
        logger_text = f"Trying to send probes: {data} ... "
        response = requests.post(
            url=url,
            headers={'Content-type': 'application/json'},
            data=json.dumps({'device_id': device_number,
                             'analyzer': device_name,
                             'data': data.decode(encoding=encoding_type),
                             'port_parameters': port_parameters,
                             }),
            timeout=100,
        )
    except OSError as ex:
        logger_text += "OSError!"
        logger.error(logger_text)
        logger.error(f"Data: \n{data}")
        logger.error(f"OSError is raised: {ex}")
        status['status'] = f"OSError is raised: {ex.__context__}"
    except Exception as ex:
        logger_text += "Exception!"
        logger.error(logger_text)
        logger.error(f"Data: \n{data}")
        logger.exception(f"Exception is raised: {ex}")
        status['status'] = f"Exception is raised: {ex.__context__}"
    else:
        # если данные приняты прокси сервером
        if response.status_code == 200:
            logger_text += "Success!"
            logger.info(logger_text)
        # если прокси сервер не принял данные
        else:
            logger_text += f"{response.content.decode()}!"
            logger.error(logger_text)

        status['status'] = response.status_code


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
