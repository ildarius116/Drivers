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
        date_time = datetime.strptime(data[6], '%Y%m%d%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['message_date'] = date_time
        tmp_data['message_type'] = data[8]
        tmp_data['message_control_id'] = data[9]
        tmp_data['processing_id'] = data[10]
        tmp_data['version_HL7_protocol'] = data[11]
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
        try:
            patient_ID_list = data[3].split("^")
            tmp_data['patient_ID'] = patient_ID_list[0]
        except:
            tmp_data['patient_ID'] = ''
        try:
            tmp_data['patient_name'] = data[5]
        except:
            tmp_data['patient_name'] = ''

        # TODO
        #  тесты кодировки кириллицы
        try:
            print(f"patient_name: {data[5]}")
            print(f"patient_name b'data[5]': {data[5].encode()}")
        except:
            pass
        try:
            print(f"patient_name 'utf-8': {data[5].encode().decode(encoding='utf-8')}")
        except:
            pass
        try:
            print(f"patient_name 'windows-1251': {data[5].encode().decode(encoding='windows-1251')}")
        except:
            pass

        try:
            tmp_data['birth_date'] = data[7]
        except:
            tmp_data['birth_date'] = ''
        try:
            tmp_data['gender'] = data[8]
        except:
            tmp_data['gender'] = ''
    except Exception as ex:
        logger.exception(f"patient_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
        results = []
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['patient_info'] = tmp_data
    return results


def patient_visit_handler(data: list, results: list) -> list:
    """
    Функция обработки данных пациента.

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        try:
            tmp_data['patient_class'] = data[2]
        except:
            tmp_data['patient_class'] = ''
        try:
            tmp_data['patient_location'] = data[3]
        except:
            tmp_data['patient_location'] = ''
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
        tmp_data['order_number'] = data[3]
        tmp_data['range_id_number'] = data[4]
        sample_id, sample_name, encode_sys = data[4].split('^')
        tmp_data['sample_id'] = sample_id
        tmp_data['sample_name'] = sample_name
        tmp_data['encode_sys'] = encode_sys
        date_time = datetime.strptime(data[7], '%Y%m%d%H%M%S').strftime('%Y-%m-%dT%H:%M:%S')
        tmp_data['test_time'] = date_time
        tmp_data['diagnosis_maker'] = data[24]
        tmp_data['principal_result_interpreter'] = data[32]
    except Exception as ex:
        logger.exception(f"request_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['order_info'] = tmp_data
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
        mnemonic = data[3]
        tmp_data['mnemonics_code'] = mnemonic[0]
        tmp_data['mnemonics_name'] = mnemonic[1]
        tmp_data['encode_sys'] = mnemonic[2]
        tmp_data['result'] = data[5]
        tmp_data['units'] = data[6]
        tmp_data['references_range'] = data[7]
        tmp_data['flag'] = data[8]
        tmp_data['result_status'] = data[11]
    except Exception as ex:
        logger.exception(f"results_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['probe_results'].append(tmp_data)
    return results


def comments_handler(data: list, results: list) -> list:
    """
    Функция обработки данных Test Order

    :return:
        results - словарь с содержимым результатов анализа

    """
    tmp_data = {}
    try:
        tmp_data['order_control'] = data[1]
        tmp_data['placer_order_number'] = data[2]
        tmp_data['filler_order_number'] = data[3]
        tmp_data['order_status'] = data[5]
    except Exception as ex:
        logger.exception(f"test_order_handler ERROR ... Received data: {data}")
        logger.exception(f"Exception is: {ex}")
    # запись временных данных в общий шаблон результатов анализа
    results[-1]['test_order_info'] = tmp_data
    return results


def split_line(data: str, results: list) -> list:
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
    elif 'PV1' in data[0]:
        # print(f"patient_handler data: {data}")
        results = patient_visit_handler(data, results)
    elif 'OBR' in data[0]:
        # print(f"report_handler data: {data}")
        results = report_handler(data, results)
    elif 'OBX' in data[0]:
        # print(f"results_handler data: {data}")
        results = results_handler(data, results)
    elif 'ORC' in data[0]:
        # print(f"query_definition_handler data: {data}")
        results = comments_handler(data, results)
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
        elif 'PV1' in line:
            results = split_line(line, results)
        elif 'OBR' in line:
            results = split_line(line, results)
        elif 'OBX' in line:
            results = split_line(line, results)
        elif 'ORC' in line:
            results = split_line(line, results)
        # все прочие сообщения
        else:
            # print('create_data else line:', line)
            pass


if __name__ == '__main__':
    pass
