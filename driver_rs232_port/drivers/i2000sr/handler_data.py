import re
import logging
from datetime import datetime

# конфигурирование логгера
logger = logging.getLogger(__name__)

STX = bytes.fromhex("02")
ETX = bytes.fromhex("03")
EOT = bytes.fromhex("04")
ENQ = bytes.fromhex("05")
ACK = bytes.fromhex("06")
LF = bytes.fromhex("0A")
CR = bytes.fromhex("0D")
NAK = bytes.fromhex("15")
ETB = bytes.fromhex("17")


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
    }
    try:
        tmp_data['analyzer_name'] = data[5]
        tmp_data['software_version'] = data[6]
        tmp_data['analyzer_serial'] = data[7]
        tmp_data['interface_version'] = data[8]
        tmp_data['transmission_date_raw'] = data[-1]
        date_time = datetime.strptime(data[-1], '%Y%m%d%H%M%S')
        date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['transmission_date'] = date_time
    except Exception as ex:
        logger.exception(f"header_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results_pattern['probe_header'] = tmp_data
    results.append(results_pattern)
    return results


def request_handler(data: list, results: list) -> list:
    """
    Функция обработки данных заголовка анализа.

    :param
        data - список данных анализа
        results - словарь с содержимым результатов анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    tmp_data = {}
    try:
        tmp_data['sample_id'] = data[3]
        tmp_data['test_id'] = data[8]
        # запись временных данных в общий шаблон результатов анализа
        results[-1]['request_info']["Q"] = tmp_data
    except Exception as ex:
        logger.exception(f"request_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
        results[-1]['request_info'] = tmp_data
    return results


def patient_handler(data: list, results: list) -> list:
    """
    Функция обработки данных пациента

    :param
        data - список данных анализа
        results - словарь с содержимым результатов анализа

    :return:
        results - словарь с содержимым результатов анализа
    """
    tmp_data = {}
    if len(data) > 9:
        try:
            tmp_data['Second_name'] = data[5]
            tmp_data['First_name'] = data[6]
            tmp_data['Patronymic'] = data[7]
            tmp_data['Birth_date'] = data[9]
            tmp_data['Gender'] = data[10]
        except Exception as ex:
            logger.exception(f"patient_handler ERROR ... Received data: {data}")
            logger.exception(f"Exception is: {ex}")
    else:
        tmp_data['Second_name'] = ''
        tmp_data['First_name'] = ''
        tmp_data['Patronymic'] = ''
        tmp_data['Birth_date'] = ''
        tmp_data['Gender'] = ''
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['patient_info'] = tmp_data
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
    assay_status = {'P': 'primary version', 'C': 'correlation version'}
    priority = {'S': 'STAT', 'R': 'Routine'}
    report_type = {'F': 'Final Result', 'X': 'Test could not be performed'}
    try:
        if data[3]:
            tmp_data['sample_id'] = data[2]
            tmp_data['sample_carousel_id'] = data[4]
            tmp_data['sample_position'] = data[5]
            tmp_data['test_code'] = data[9]
            tmp_data['test_name'] = data[10]
            tmp_data['assay_protocol'] = data[11]
            tmp_data['assay_status'] = assay_status[data[12]]
            tmp_data['priority'] = priority[data[13]]
            if 'Q' in data[15]:
                tmp_data['action_code'] = 'Quality Control result'
            else:
                tmp_data['action_code'] = 'Patient result'
            tmp_data['report_type'] = report_type[data[-1]]
        else:
            tmp_data['sample_id'] = data[2]
            tmp_data['test_code'] = data[7]
            tmp_data['priority'] = priority[data[8]]
            tmp_data['note'] = data[14]
            if 'Q' in data[28]:
                tmp_data['action_code'] = 'Quality Control result'
            else:
                tmp_data['action_code'] = 'Patient result'
    except Exception as ex:
        logger.exception(f"test_order_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['test_order_info'] = tmp_data
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
    comment_type = {'G': 'Result Comment', 'I': 'Exception String'}
    try:
        tmp_data['comment'] = data[3]
        tmp_data['comment_type'] = comment_type[data[4]]
        # запись временных данных в общий шаблон результатов анализа
        results[-1]['probe_comments'][data[0]] = tmp_data
    except Exception as ex:
        logger.exception(f"comments_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
        # запись временных данных в общий шаблон результатов анализа
        results[-1]['probe_comments'] = tmp_data
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
    assay_status = {'P': 'primary version', 'C': 'correlation version'}
    result_type = {'F': 'Final result', 'P': 'Preliminary result', 'I': 'Interpretation of results'}
    abnormal_flags = ['IUO', 'EDIT', '1-2s', '1-3s', '2-2s1R1M', '2-2s1RxM', '2-2sxR1M', 'R-4s', '4-1s1M', '4-1sxM',
                      '10-x1M', '10-xxM', 'EXP', 'EXPC', 'A#1', 'A#2', 'CNTL', '<', '>', 'INDX', 'FLEX', 'LL', 'HH',
                      'PSHH', 'LOW', 'HIGH', 'CORR']
    result_status = {'F': 'Final Result', 'R': 'Previously Transmitted Results'}
    offset = 0
    try:
        tmp_data['test_code'] = data[5]
        tmp_data['test_name'] = data[6]
        tmp_data['assay_protocol'] = data[7]
        tmp_data['assay_status'] = assay_status[data[8]]
        tmp_data['reagent_lot'] = data[9]
        tmp_data['reagent_ser_num'] = data[10]
        tmp_data['control_lot_num'] = data[11]
        tmp_data['result_type'] = result_type[data[12]]
        tmp_data['result'] = data[13]
        tmp_data['units'] = data[14]
        if data[15]:
            tmp_data['range'] = data[15]
        if data[16]:
            flag = False
            tmp_data['flags'] = []
            for i in range(16, len(data) - 5):
                if data[i] in abnormal_flags:
                    tmp_data['flags'].append(data[i])
                    if flag:
                        offset += 1
                    else:
                        flag = True
                else:
                    break
        tmp_data['result_status'] = result_status[data[18 + offset]]
        tmp_data['operator'] = data[20 + offset]
        date_time = datetime.strptime(data[23 + offset], '%Y%m%d%H%M%S')
        date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['probe_date'] = date_time
        results[-1]['probe_date'] = date_time
        tmp_data['module_serial_number'] = data[24 + offset]
    except Exception as ex:
        logger.exception(f"results_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")

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
    try:
        # выделение сервисной части сообщения
        data = re.findall(pattern, line)[0]
        # превращение её в список
        data = re.split(r'[|^]', data)
    except Exception as ex:
        logger.exception(f"split_line Exception split ... \nReceived line: {line} \nPattern: {pattern}")
        logger.exception(f"Exception is: {ex}")
        data = []
    try:
        if 'H' in data[0]:
            results = header_handler(data, results)
        elif 'P' in data[0]:
            results = patient_handler(data, results)
        elif 'Q' in data[0]:
            results = request_handler(data, results)
        elif 'O' in data[0]:
            results = test_order_handler(data, results)
        elif 'R' in data[0]:
            results = results_handler(data, results)
        elif 'C' in data[0]:
            results = comments_handler(data, results)
    except Exception as ex:
        logger.exception(f"split_line Exception in data[0] ... \nReceived line: {line} \nPattern: {pattern}")
        logger.exception(f"Exception is: {ex}")
    return results


def create_data(lines: list) -> list:
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
            results = []
        # сообщение о завершении передачи сообщений
        elif '<EOT>' in line:
            return results
        # все прочие сообщения
        else:
            pattern = r"\\x02(.*)\\r\\x03"
            results = split_line(line, pattern, results)
    return results


if __name__ == '__main__':
    with open('../emulators/logs/Architect_i2000SR_clear.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    res = main(content)
