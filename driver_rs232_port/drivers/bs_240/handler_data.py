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
        "patient_info": {},
        "test_order_info": {},
        "probe_results": [],
        "probe_comments": {},
        "query_definition": {},
        "query_filter": {},
    }
    try:
        tmp_data['manufacturer'] = data[2]
        tmp_data['analyzer_name'] = data[3]
        date_time = datetime.strptime(data[6], '%Y%m%d%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['message_date'] = date_time
        tmp_data['message_type'] = data[8]
        tmp_data['message_control_id'] = data[9]
        tmp_data['processing_id'] = data[10]
        tmp_data['version_HL7_protocol'] = data[11]
        application_type = data[15]
        if application_type == '2':
            tmp_data['QC_result'] = 'true'
        else:
            tmp_data['QC_result'] = 'false'
        tmp_data['character_set'] = data[17]
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

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['patient_ID'] = data[2]
        tmp_data['patient_name'] = data[5]
        tmp_data['birth_date'] = data[7]
        tmp_data['gender'] = data[8]
    except Exception as ex:
        logger.exception(f"patient_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
        results = []
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['patient_info'] = tmp_data
    return results


def report_handler(data: list, results: list) -> list:
    """
    Функция обработки данных заголовка анализа.

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['sample_bar_code'] = data[2]
        tmp_data['sample_id'] = data[3]
        tmp_data['range_id_number'] = data[4]
        company, product = data[4].split('^')
        tmp_data['company'] = company
        tmp_data['product'] = product
        tmp_data['emergency'] = data[5]
        date_time = datetime.strptime(data[6], '%Y%m%d%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['test_time'] = date_time
        tmp_data['specimen_action_code'] = data[10]
        tmp_data['danger_code'] = data[11]
        tmp_data['ordering_provider'] = data[15]
    except Exception as ex:
        logger.exception(f"request_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['observer_info'] = tmp_data
    return results


def results_handler(data: list, results: list) -> list:
    """
    Функция обработки данных результатов анализа.

    :return:
        results - словарь с содержимым результатов анализа

    """
    flags_dict = {'N': '', 'L': 'Low', 'H': 'High', }
    tmp_data = {}
    try:
        tmp_data['value_type'] = data[2]
        tmp_data['mnemonics_code'] = data[3]
        tmp_data['mnemonics_name'] = data[4]
        tmp_data['result'] = data[5]
        tmp_data['units'] = data[6]
        tmp_data['references_range'] = data[7]
        tmp_data['flag'] = flags_dict.get(data[8], '')
        tmp_data['probability'] = data[9]
        tmp_data['result_status'] = data[11]
        tmp_data['user_result'] = data[13]
        date_time = datetime.strptime(data[14], '%Y%m%d%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['last_normal_result_date'] = date_time
    except Exception as ex:
        logger.exception(f"results_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['probe_results'].append(tmp_data)
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
        tmp_data['specimen_type'] = data[20]
        tmp_data['specimen_subtype'] = data[21]
        tmp_data['result_status'] = data[-1]
    except Exception as ex:
        logger.exception(f"test_order_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['test_order_info'] = tmp_data
    return results


def query_definition_handler(data: list, results: list) -> list:
    """
    Функция обработки данных заголовка анализа.

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        date_time = datetime.strptime(data[1], '%Y%m%d%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['query_date'] = date_time
        tmp_data['query_format_code'] = data[2]
        tmp_data['query_priority'] = data[3]
        tmp_data['query_id'] = data[4]
        tmp_data['quantity_limited_request'] = data[7]
        # Field 8 is bar code for real-time downloading and null for group downloading
        tmp_data['sample_bar_code'] = data[8]
        tmp_data['OTH_for_query'] = data[9]
        tmp_data['query_results_level'] = data[12]
    except Exception as ex:
        logger.exception(f"request_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['query_definition'] = tmp_data
    return results


def query_filter_handler(data: list, results: list) -> list:
    """
    Функция обработки данных заголовка анализа.

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['object_type'] = data[6]
        tmp_data['object_status'] = data[7]
        tmp_data['date_time_selection_qualifier'] = data[8]
    except Exception as ex:
        logger.exception(f"request_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['query_filter'] = tmp_data
    return results


def split_line(data: str, results: list, pattern: str = None) -> list:
    """
    Функция делит полученную строку на строки с данными анализа и его результаты
    """
    # превращение её в список
    data = re.split(r'[|]', data)

    if 'MSH' in data[0]:
        # print(f"header_handler data: {data}")
        results = header_handler(data, results)
    elif 'PID' in data[0]:
        # print(f"patient_handler data: {data}")
        results = patient_handler(data, results)
    elif 'OBR' in data[0]:
        # print(f"report_handler data: {data}")
        results = report_handler(data, results)
    elif 'OBX' in data[0]:
        # print(f"results_handler data: {data}")
        results = results_handler(data, results)
    elif 'QRD' in data[0]:
        # print(f"query_definition_handler data: {data}")
        results = query_definition_handler(data, results)
    elif 'QRF' in data[0]:
        # print(f"query_filter_handler data: {data}")
        results = query_filter_handler(data, results)
    return results


def create_data(lines: (str, bytes)) -> list:
    """
    Основная функция (первичной) обработки полученных данных
    """
    results = []
    for line in lines:
        # сообщение о начале передачи сообщений
        if '<ENQ>' in line:
            # print('Start transmitting')
            results = []
        # сообщение о завершении передачи сообщений
        elif '<EOT>' in line:
            # print('Stop transmitting')
            return results
        # сообщение о завершении передачи сообщений
        elif 'MSH' in line:
            results = split_line(line, results)
        elif 'PID' in line:
            results = split_line(line, results)
        elif 'OBR' in line:
            results = split_line(line, results)
        elif 'OBX' in line:
            results = split_line(line, results)
        elif 'QRD' in line:
            results = split_line(line, results)
        elif 'QRF' in line:
            results = split_line(line, results)
        # все прочие сообщения
        else:
            # print('create_data else line:', line)
            pass


if __name__ == '__main__':
    # временное считывание логов из файла
    with open('logs/CD_Ruby2_full.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    create_data(content)
