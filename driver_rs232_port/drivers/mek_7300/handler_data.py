import re
import logging
from datetime import datetime

# конфигурирование логгера
logging.basicConfig(level=logging.INFO,
                    # filename='logger.log',
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )
logger = logging.getLogger(__name__)


def header_handler(data: list, results: dict) -> dict:
    """
    Функция обработки данных заголовка анализа.

    :return:
        results - словарь с содержимым результатов анализа

    """
    # logger.info(f"Received converted data:")
    tmp_data = {}
    tmp_data['analyzer_name'] = data[5]
    tmp_data['analyzer_number'] = data[6]
    tmp_data['analyzer_serial_number'] = data[7]
    tmp_data['software_version_1'] = data[8]
    tmp_data['software_version_2'] = data[9]
    tmp_data['processing_ID'] = data[-3]
    tmp_data['ASTM_version_No'] = data[-2]
    date_time = datetime.strptime(data[-1], '%Y%m%d%H%M%S')
    date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
    tmp_data['transmission_date'] = date_time

    # запись временных данных в общий шаблон результатов анализа
    results['probe_header'] = tmp_data
    return results


def patient_handler(data: list, results: dict) -> dict:
    """
    Функция обработки данных пациента.

    :return:
        results - словарь с содержимым результатов анализа

    """
    logger.info(f"patient_handler Received data: {data}")
    logger.info(f"patient_handler Received results: {results}")
    tmp_data = {}
    tmp_data['patient_ID'] = data[4]
    # tmp_data['info_2'] = data[5]
    # tmp_data['info_3'] = data[13]
    # tmp_data['info_4'] = data[14]
    # tmp_data['info_4'] = data[-1]
    # запись временных данных в общий шаблон результатов анализа
    results['patient_info'] = tmp_data
    return results


def comments_handler(data: list, results: dict) -> dict:
    """
    Функция обработки данных комментария.

    :return:
        results - словарь с содержимым результатов анализа

    """
    # logger.info(f"Received converted data:")
    tmp_data = {}
    if len(data) == 7:
        tmp_data['comment_source'] = data[2]
        tmp_data['def_add_info'] = data[3]
        tmp_data['add_info_1'] = data[4]
        tmp_data['add_info_2'] = data[5]
        tmp_data['comment_type'] = data[6]
    else:
        tmp_data['comment_source'] = data[2]
        tmp_data['def_add_info'] = data[3]
        tmp_data['add_info_1'] = data[4]
        tmp_data['add_info_2'] = None
        tmp_data['comment_type'] = data[5]

    # запись временных данных в общий шаблон результатов анализа
    results['probe_comments'][data[0]] = tmp_data
    return results


def test_order_handler(data: list, results: dict) -> dict:
    """
    Функция обработки данных Test Order

    :return:
        results - словарь с содержимым результатов анализа

    """
    # logger.info(f"Received converted data:")
    tmp_data = {}
    # print(f"test_order_handler data: {data}")
    # print(f"test_order_handler specimen_ID: {data[2]}")
    specimen_ID = data[2].replace("`", "")
    # print(f"test_order_handler specimen_ID: {specimen_ID}")
    tmp_data['specimen_ID'] = specimen_ID
    tmp_data['rack_ID'] = data[3]
    tmp_data['rack_pos'] = data[4]
    tmp_data['sequential_ID'] = data[5]
    tmp_data['specimen_type_name'] = data[17]
    tmp_data['specimen_type_number'] = data[18]
    date_time = datetime.strptime(data[-4], '%Y%m%d%H%M%S')
    date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
    tmp_data['probe_date'] = date_time
    tmp_data['report_type'] = data[-1]
    # запись временных данных в общий шаблон результатов анализа
    results['test_order_info'] = tmp_data
    return results


def results_handler(data: list, results: dict) -> dict:
    """
    Функция обработки данных результатов анализа.

    :return:
        results - словарь с содержимым результатов анализа

    """
    # logger.info(f"Received converted data:")
    tmp_data = {}
    parameter_codes = {
        '2A0100000019301': 'WBC',
        '2A0200000019301': 'RBC',
        '2A0300000019301': 'HGB',
        '2A0400000019301': 'HCT',
        '2A0600000019301': 'MCV',
        '2A0700000019301': 'MCH',
        '2A0800000019301': 'MCHC',
        '2A0500000019301': 'PLT',
    }
    tmp_data['code'] = data[4]
    tmp_data['standard'] = data[6]
    tmp_data['mnemonics'] = data[5]

    if data[4]:
        tmp_data['result'] = data[7]
        tmp_data['units'] = data[8]
        tmp_data['range'] = data[11]
    else:
        tmp_data['result'] = data[6]
        tmp_data['units'] = data[7]
        tmp_data['range'] = data[10]

    tmp_data['analyzer_name'] = data[-1]
    probe_date = results['test_order_info']['probe_date']
    tmp_data['probe_date'] = probe_date

    # запись временных данных в общий шаблон результатов анализа
    results['probe_results'][f'{data[0]}|{data[1]}'] = tmp_data
    return results


def split_line(line: str, pattern: str, results: dict) -> dict:
    """
    Функция делит полученную строку на строки с сервисными данными анализа и его результаты
    """
    # выделение сервисной части сообщения
    data = re.findall(pattern, line)[0]
    # print('data:', data)
    # превращение её в список
    data = re.split(r'[|^]', data)
    # print('data:', data)

    if 'H' in data[0]:
        # print('\nline:', line.replace('\n', ''))
        # print('data:', data)
        results = header_handler(data, results)
        # print('results:', results)
        pass
    elif 'P' in data[0]:
        # print('\nline:', line.replace('\n', ''))
        # print('data:', data)
        results = patient_handler(data, results)
        # print('results:', results)
        pass
    elif 'O' in data[0]:
        # print('\nline:', line.replace('\n', ''))
        # print('data:', data)
        results = test_order_handler(data, results)
        # print('results:', results)
        pass
    elif 'C' in data[0]:
        # print('\nline:', line.replace('\n', ''))
        # print('data:', data)
        results = comments_handler(data, results)
        # print('results:', results)
        pass
    elif 'R' in data[0]:
        # print('\nline:', line.replace('\n', ''))
        # print('data:', data)
        results = results_handler(data, results)
        # print('results:', results)
        pass
    return results


def create_data(lines: list) -> dict:
    """
    Основная функция (первичной) обработки полученных данных
    """
    # print(data)
    results = {}
    # print('lines_main:', lines)
    for line in lines:
        # print('\nline:', line.replace('\n', ''))
        # print('line:', line)
        # сообщение о начале передачи сообщений
        if '<ENQ>' in line:
            # print('Start transmitting')
            # шаблон для результатов анализа
            results = {
                "probe_header": None,
                "patient_info": None,
                "test_order_info": None,
                "probe_results": {},
                "probe_comments": {},
                "request_info": None
            }
            pass
        # сообщение о завершении передачи сообщений
        elif '<EOT>' in line:
            # print('Stop transmitting')
            return results
            pass
        # все прочие сообщения
        else:
            # print('line:', line.replace('\n', ''))
            pattern = r"<STX>(.*)<CR><ETX>"
            pattern = r"\x02(.*)\r\x03"
            results = split_line(line, pattern, results)
            # print('res:', results)
    return results


if __name__ == '__main__':
    # TODO
    # временное считывание логов из файла
    with open('../emulators/logs/MEK7300_full.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()

    main(content)
