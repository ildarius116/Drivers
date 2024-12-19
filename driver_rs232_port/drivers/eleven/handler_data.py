import re
import logging
from datetime import datetime

# конфигурирование логгера
logger = logging.getLogger(__name__)


def header_handler(data: list, results: list) -> list:
    """
    Функция обработки данных заголовка анализа

    :param
        data - список данных анализа
        results - словарь с содержимым результатов анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    tmp_data = {}
    # шаблон для результатов анализа
    results_pattern = {
        "probe_header": None,
        "patient_info": None,
        "test_order_info": {},
        "probe_results": [],
        "probe_comments": {},
        "request_info": {},
        "last_order": None
    }
    try:
        tmp_data['analyzer_name'] = data[5]
        tmp_data['analyzer_number'] = data[6]
        tmp_data['analyzer_ver'] = data[7]
        # tmp_data['probe_number'] = data[4]
        date_time = datetime.strptime(data[16], '%Y%m%d%H%M%S')
        date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['transmission_date'] = date_time
    except Exception as ex:
        logger.exception(f"header_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results_pattern['probe_header'] = tmp_data
    results.append(results_pattern)
    return results


def patient_handler(data: list, results: list) -> list:
    """
    Функция обработки данных пациента.

    :param
        data - список данных анализа
        results - словарь с содержимым результатов анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    tmp_data = {}
    try:
        tmp_data['sequence_number'] = data[1]
    except Exception as ex:
        logger.exception(f"patient_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
        results = []
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['patient_info'] = tmp_data
    return results


def comments_handler(data: list, results: list) -> list:
    """
    Функция обработки данных комментария.

    :param
        data - список данных анализа
        results - словарь с содержимым результатов анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    tmp_data = {}
    try:
        if 'Flag' in data[3]:
            tmp_data['pathology'] = data[3]
            tmp_data['result_number'] = data[4]
            tmp_data['diagnosis'] = data[5]
        else:
            tmp_data['param_type'] = data[3]
            tmp_data['parameter'] = data[4]
            tmp_data['mnemonics'] = data[5]
    except Exception as ex:
        logger.exception(f"comments_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['probe_comments'][data[0]] = tmp_data
    return results


def test_order_handler(data: list, results: list) -> list:
    """
    Функция обработки данных Test Order

    :param
        data - список данных анализа
        results - словарь с содержимым результатов анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    tmp_data = {}
    try:
        try:
            # если номер пробы - это не число, то записать пустую строку
            bar_code = int(data[2])
        except:
            bar_code = ''
        tmp_data['bar_code_ID'] = bar_code
        tmp_data['probe_number'] = data[3]
        tmp_data['probe_type'] = data[7]
        tmp_data['priority'] = data[8]
        tmp_data['sample_type'] = data[18]
        tmp_data['comment_1'] = data[22]
        tmp_data['comment_2'] = data[23]
    except Exception as ex:
        logger.exception(f"test_order_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['test_order_info'] = tmp_data
    return results


def results_handler(data: list, results: list) -> list:
    """
    Функция обработки данных результатов анализа.

    :param
        data - список данных анализа
        results - словарь с содержимым результатов анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    tmp_data = {}
    try:
        tmp_data['mnemonics'] = f'{data[6]}'
        if data[7] and data[8]:
            tmp_data['result'] = f'{data[7]}^{data[8]}'
        elif data[7]:
            tmp_data['result'] = f'{data[7]}'
        elif data[8]:
            tmp_data['result'] = f'{data[8]}'
        if len(data) == 16:
            tmp_data['units'] = data[9]
            tmp_data['result_status'] = data[12]
            date_time = datetime.strptime(data[15], '%Y%m%d%H%M%S')
            date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
            tmp_data['result_date'] = date_time
        else:
            tmp_data['units'] = data[-3]
            tmp_data['result_status'] = ''
            if '*' in data[-1]:
                data[-1] = data[-1].replace('*', '')
                tmp_data['flags'] = True
            try:
                date_time = datetime.strptime(data[-1], '%Y%m%d%H%M%S')
                date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
            except:
                date_time = datetime.strptime(data[-1], '%Y%m%d%H%M')
                date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
            tmp_data['result_date'] = date_time
    except Exception as ex:
        logger.exception(f"results_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['probe_results'].append(tmp_data)
    return results


def split_line(line: str, pattern: str, results: list) -> list:
    """
    Функция делит полученную строку на строки с сервисными данными анализа и его результаты

    :param
        line - строка данных анализа
        pattern - шаблон поиска данных в строке
        results - словарь с содержимым результатов анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    # выделение сервисной части сообщения
    try:
        try:
            data = re.findall(pattern, line)[0]
        except IndexError:
            # pattern = r"\x02(.*)\r\x17"
            pattern = r"\x02(.*)\r\x03"
            pattern = r"\\x02(.*)\\r\\x03"


            data = re.findall(pattern, line)[0]

        # превращение её в список
        data = re.split(r'[|^]', data)
    except Exception as ex:
        logger.exception(f"split_line ERROR ... \nReceived line: {line} \nPattern: {pattern}")
        logger.exception(ex)
        data = []

    if 'H' in data[0]:
        results = header_handler(data, results)
    elif 'P' in data[0]:
        results = patient_handler(data, results)
    elif 'O' in data[0]:
        results = test_order_handler(data, results)
    elif 'C' in data[0]:
        results = comments_handler(data, results)
    elif 'R' in data[0]:
        results = results_handler(data, results)
    return results


def create_data(lines: (str, bytes)) -> list:
    """
    Основная функция (первичной) обработки полученных данных

    :param
        line - список строк данных анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    results = []
    for line in lines:
        # сообщение о начале передачи сообщений
        if '<ENQ>' in line:
            # шаблон для результатов анализа
            results = []
        # сообщение о завершении передачи сообщений
        elif '<EOT>' in line:
            return results
        # все прочие сообщения
        else:
            # pattern = r"\x02(.*)\r\x03"
            pattern = r"\\x02(.*)\\r\\x17"
            results = split_line(line, pattern, results)
    return results


if __name__ == '__main__':
    # временное считывание логов из файла
    with open('../emulators/logs/Eleven_clear.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    create_data(content)
