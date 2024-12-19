import os
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


def send_soap(semaphore: threading, forcibly: bool = False):
    """
    Функция посылает результаты анализа проб в LIS

    :param
            forcibly - принудительная отправка ВСЕХ результатов из БД
    :return: status - словарь с результатом отправки каждой посылки
    """
    # максимальное количество попыток отправки элемента из БД
    max_tries = os.getenv('MAX_TRIES')
    if not max_tries:
        max_tries = 3
    else:
        max_tries = int(max_tries)
    # адрес ЛИС сервера
    url = os.getenv('LIS_URL')
    # логин и пароль сервера
    authentication = eval(os.getenv('AUTH'))
    # заголовок сообщения
    headers = {'Content-Type': 'text/xml; charset=utf-8'}

    probes_list = []
    status = {'status': []}
    while True:
        # создание списка отчетов из имеющихся в буферной БД
        semaphore.acquire()
        probes_is_in_buffer = Analyzes.get_all_analyzes_with_probe_results()
        semaphore.release()
        for n, probe in enumerate(probes_is_in_buffer):
            # если ПРИНУДИТЕЛЬНО или колонка ПОПЫТКИ пустая или КОЛИЧЕСТВО ПОПЫТОК меньше максимального
            if forcibly or not probe.tries or probe.tries < max_tries:
                probes_list.append(probe.probe_results)
                # получаем данные в СОАП формате для LISа из БД
                probe_result = probe.probe_results
                # попытка отправить все имеющиеся в памяти отчеты
                try:
                    logger.info("Trying to send probes:")
                    response = requests.request(method="POST",
                                                url=url,
                                                headers=headers,
                                                data=probe_result,
                                                auth=authentication,
                                                timeout=80)
                except OSError as ex:
                    logger.info(f"Data: \n{probe_result}")
                    logger.error(f"OSError is raised: {ex}")
                    status['status'].append({n: f"Exception is raised: {ex.__context__}"})
                except Exception as ex:
                    logger.info(f"Data: \n{probe_result}")
                    logger.exception(f"Exception is raised: {ex}")
                    status['status'].append({n: f"Exception is raised: {ex.__context__}"})

                else:
                    # если статус код = 200, значит данные были приняты и можно из буфера текущие результаты
                    if response.status_code == 200:
                        semaphore.acquire()
                        delete_analyze(probe)
                        semaphore.release()
                        logger.info(f"Data: \n{probe_result}")
                        logger.info(f"status_code: {response.status_code}")
                        logger.debug(f"Probe {probe} is deleted from buffer")
                        logger.debug(f"response.text: {response.text}")
                    # в остальных случаях, данные из буферной БД не удаляются
                    else:
                        semaphore.acquire()
                        edit_analyze(probe, error_text=str(response.text))
                        semaphore.release()
                        logger.info(f"probe.probe_results: \n{probe.probe_results}")
                        logger.info(f"Data: \n{probe_result}")
                        logger.warning(f"status_code: {response.status_code}")
                        logger.warning(f"Probes buffer is not cleared")
                        logger.warning(f"response.text: {response.text}")
                    status['status'].append({n: response.status_code})
        sleep(0.1)
    # return status


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
