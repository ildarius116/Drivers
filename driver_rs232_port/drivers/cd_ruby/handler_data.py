import re
import logging

from datetime import datetime

# конфигурирование логгера
logger = logging.getLogger(__name__)


def header_handler(data: list, results: list) -> list:
    """
    Функция обработки данных заголовка анализа.

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
        tmp_data['analyzer_name'] = data[7]
        tmp_data['analyzer_number'] = data[6]
        tmp_data['software_version'] = data[7]
        tmp_data['host_computer_version_ID'] = data[8]
        tmp_data['processing_ID'] = data[-2]
        tmp_data['CLSI_version_No.'] = data[-1]
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

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['range_ID_number'] = data[3]
    except Exception as ex:
        logger.exception(f"request_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['request_info'] = tmp_data
    return results


def patient_handler(data: list, results: list) -> list:
    """
    Функция обработки данных пациента.

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['patient_ID'] = data[3]
        tmp_data['patient_name'] = data[5]
        tmp_data['birth_date'] = data[7]
        tmp_data['gender'] = data[8]
        tmp_data['doctor'] = data[11]
        tmp_data['note_1'] = data[13]
        tmp_data['note_2'] = data[14]
    except Exception as ex:
        logger.exception(f"patient_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
        results = []
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['patient_info'] = tmp_data
    return results


def test_order_handler(data: list, results: list) -> list:
    """
    Функция обработки данных Test Order

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        try:
            tmp_data['sample_id'] = int(data[2])
            tmp_data['test_name'] = data[3]
            if data[3] and not data[4]:
                try:
                    tmp_data['test_ID'] = int(data[3])
                except:
                    tmp_data['test_ID'] = data[4]
            else:
                tmp_data['test_ID'] = data[4]
        except:
            tmp_data['sample_id'] = ''
            tmp_data['test_name'] = data[2]
            if data[2] and not data[3]:
                try:
                    tmp_data['test_ID'] = int(data[2])
                except:
                    tmp_data['test_ID'] = data[3]
            else:
                tmp_data['test_ID'] = data[3]

        tmp_data['test_type'] = data[5]
        tmp_data['test_selection'] = data[7]
        tmp_data['parameter_set_selection'] = data[8]
        tmp_data['limit_set_selection'] = data[9]
        # date_time = datetime.strptime(data[12], '%Y%m%d%H%M%S')
        # date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
        # tmp_data['probe_date'] = date_time
        tmp_data['specimen_type'] = data[20]
        tmp_data['specimen_subtype'] = data[21]
        tmp_data['result_status'] = data[-1]
    except Exception as ex:
        logger.exception(f"test_order_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['test_order_info'] = tmp_data
    return results


def comments_handler(data: list, results: list) -> list:
    """
    Функция обработки данных комментария.

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['comment_source'] = data[3]
        tmp_data['comment_text'] = data[4]
        tmp_data['comment_type'] = data[5]
    except Exception as ex:
        logger.exception(f"comments_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['probe_comments'][data[0]] = tmp_data
    return results


def results_handler(data: list, results: list) -> list:
    """
    Функция обработки данных результатов анализа.

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['test_selection'] = data[5]
        tmp_data['parameter_set_selection'] = data[6]
        tmp_data['limit_set_selection'] = data[7]
        tmp_data['mnemonics'] = data[8]
        tmp_data['result'] = data[9]
        tmp_data['result_status'] = data[14]
        tmp_data['operator'] = data[16]
        date_time = datetime.strptime(data[17], '%Y%m%d%H%M%S')
        date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['result_date'] = date_time
        tmp_data['probe_date'] = date_time
        tmp_data['analyzer_number'] = data[19]
        tmp_data['flag'] = False
    except Exception as ex:
        logger.exception(f"results_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['probe_results'].append(tmp_data)
    return results


def flags_handler(data: list, results: list) -> list:
    """
    Функция обработки данных результатов анализа.

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['test_selection'] = data[5]
        tmp_data['parameter_set_selection'] = data[6]
        tmp_data['limit_set_selection'] = data[7]
        tmp_data['mnemonics'] = data[8]
        tmp_data['result'] = ''
        tmp_data['result_status'] = ''
        tmp_data['operator'] = data[16]
        date_time = datetime.strptime(data[17], '%Y%m%d%H%M%S')
        date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['result_date'] = date_time
        tmp_data['probe_date'] = date_time
        tmp_data['analyzer_number'] = data[19]
        tmp_data['flag'] = True
    except Exception as ex:
        logger.exception(f"results_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['probe_results'].append(tmp_data)
    return results


def split_line(line: str, pattern: str, results: list) -> list:
    """
    Функция делит полученную строку на строки с данными анализа и его результаты
    """
    try:
        # выделение сообщения
        line = re.findall(pattern, str(line))[0]
        # превращение его в список
        datas = line.split('\\r')
    except Exception as ex:
        logger.exception(f"split_line ERROR ... \nReceived line: {line} \nPattern: {pattern}")
        logger.exception(ex)
        datas = []

    for data in datas:
        # превращение её в список
        data = re.split(r'[|^]', data)

        if 'H' in data[0]:
            results = header_handler(data, results)
        elif 'P' in data[0]:
            results = patient_handler(data, results)
        elif 'Q' in data[0]:
            results = request_handler(data, results)
        elif 'O' in data[0]:
            results = test_order_handler(data, results)
        elif 'R' in data[0]:
            # если результат пробы - это слово 'FLAG'
            if data[9] == 'FLAG':
                # создаем результат с мнемоникой 'FLAG'
                results = flags_handler(data, results)
            # в остальных случаях
            else:
                # создаем результат с мнемоникой анализа
                results = results_handler(data, results)
        elif 'C' in data[0]:
            results = comments_handler(data, results)
    return results


def create_data(lines: (str, bytes)) -> list:
    """
    Основная функция (первичной) обработки полученных данных
    """
    # print(data)
    results = []
    for line in lines:
        # print('\nline:', line.replace('\n', ''))
        # print('main line:', line)
        # сообщение о начале передачи сообщений
        if '<ENQ>' in line:
            # print('Start transmitting')
            results = []
        # сообщение о завершении передачи сообщений
        elif '<EOT>' in line:
            # print('Stop transmitting')
            return results
        # все прочие сообщения
        else:
            pattern = r"\\x02(.*)\\r\\x03"
            results = split_line(line, pattern, results)
            # print('main results:', results)


if __name__ == '__main__':
    # временное считывание логов из файла
    with open('logs/CD_Ruby2_full.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    create_data(content)
