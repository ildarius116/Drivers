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


def split_line(line: str, results: dict) -> dict:
    """
    Функция делит полученную строку на строки с сервисными данными анализа и его результаты

    :param
        line - строка данных анализа
        results - словарь с содержимым результатов анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    # удаление '\', если оно есть
    line = line.replace("\\", '')
    # превращение полученной строки в список
    line_data = re.split(r'[|^]', line)
    # если это заголовок
    if 'H' in line_data[0]:
        # выделение названия анализатора
        GEM = re.findall(r'GEM\s\d{4}', line)[0]
        results["GEM"] = GEM
        # выделение времени отправки анализа
        date_time = datetime.strptime(line_data[-1], '%Y%m%d%H%M%S')
        date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
        results["result_date"] = str(date_time)
        # выделение идентификатора анализатора
        device_id = re.findall(r'GEM\s\d{4}(.*)GEM\s\d{4}', line)[0]
        device_id = re.findall(r'\d{3,5}', device_id)[0]
        results["device_id"] = int(device_id)
    # если это данные пробы
    elif 'P' in line_data[0]:
        # номер пробы на анализ
        results["probe_number"] = line_data[-1]
    # если это данные результата анализа пробы
    elif 'R' in line_data[0]:
        if line_data[1] == '1':
            # выделение времени проведения анализа
            date_time = datetime.strptime(line_data[-1], '%Y%m%d%H%M%S')
            date_time = date_time.strftime('%Y-%m-%dT%H:%M:%S')
            results["probe_date"] = str(date_time)
        # шаблон результатов каждого анализа
        tmp_data = {
            "mnemonics": line_data[2],
            "result": None,
            "parameter": None,
            "period_min": None,
            "Note": None,
            "Comment": None,
            "period_max": None,
        }
        # запись в каждую ячейку шаблона
        for i, data in enumerate(tmp_data.items()):
            # кроме "period_max"
            if 0 < i < 6:
                try:
                    # logger.info(f"split_line line_data: {line_data}")
                    tmp = line_data[i + 2]
                    # logger.info(f"split_line line_data[i + 2]: {line_data[i + 2]}")
                    # если данные есть, они отделяются друг от друга, если их несколько
                    tmp_splited = tmp.split(' ')
                    # logger.info(f"split_line tmp_splited: {tmp_splited}")
                    tmp_splited = [data for data in tmp_splited if data]
                    # logger.info(f"split_line tmp_splited: {tmp_splited}")

                    # проход по полученным данным (спискам данных)
                    for j, tmp in enumerate(tmp_splited):
                        try:
                            # перевод данных в тип float, если возможно
                            tmp = float(tmp)
                        except ValueError:
                            # иначе, не трогаем
                            pass
                        # если в списке только значение или оно первое
                        if j == 0:
                            tmp_data[data[0]] = tmp
                        # если это второе значение, то принудительно запись в последнюю ячейку шаблона
                        else:
                            tmp_data["period_max"] = tmp
                # если данных нет, то ячейка шаблона заполняется пустыми данными
                except IndexError:
                    tmp_data[data[0]] = None
        # запись временных данных в общий шаблон результатов анализа
        # logger.info(f"'probe_results': {tmp_data}")
        results['probe_results'][line_data[2]] = tmp_data

    # elif 'C' in data[0]:
    #     # print('line_data:', line_data)
    #     results = comments_handler(data, results)
    # elif 'O' in data[0]:
    #     # print('line_data:', line_data)
    #     results = test_order_handler(data, results)
    # elif 'Q' in data[0]:
    #     # print('line_data:', line_data)
    #     results = request_handler(data, results)

    return results


def create_data(lines: list) -> dict:
    """
    Основная функция (первичной) обработки полученных данных

    :param
        line - список строк данных анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    # шаблон для результатов анализа
    results = {"GEM": None,
               "probe_header": None,
               "patient_info": None,
               "test_order_info": {},
               "probe_results": {},
               "probe_comments": {},
               "request_info": {},
               "probe_number": None,
               "probe_date": None
               }

    result_line = ''
    # выделение данных из входной строки
    for line in lines:
        line = str(line.encode())
        line = line.replace(r"b", '')
        line = line.replace(r"'", '')
        line = line.replace(r"\x05", '')
        line = re.sub(r'\\x02\S{1}', '', line)
        line = re.sub(r'\\x\S{4}\\r\\n', '', line)
        line = re.sub(r'\^{1,3}', '', line)
        line = re.sub(r'\n', '', line)
        result_line += line

    # разделение строки ответа на строки по "темам анализа"
    new_lines = result_line.split(r'\r')
    logger.info("Received converted data:")
    for line in new_lines[:-1]:
        # сообщение о завершении передачи сообщений
        if '<EOT>' in line:
            logger.info(f"<EOT>")
            return results
        # все прочие сообщения
        else:
            # сообщение о начале передачи сообщений
            if '<ENQ>' in line:
                logger.info(f"<ENQ>")
            # прочие сообщения
            else:
                logger.info(f"main line: {line}")
            results = split_line(line, results)
    return results


if __name__ == '__main__':
    # TODO
    # временное считывание логов из файла
    with open('logs/GEM_3000_clear.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()

    res = main(content)
