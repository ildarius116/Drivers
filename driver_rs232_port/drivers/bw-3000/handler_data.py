import re
import logging
from datetime import datetime
import time

# конфигурирование логгера
logger = logging.getLogger(__name__)


def chemistry_record(mnemonics, results):
    result = {}
    result['mnemonics'] = mnemonics

    if isinstance(results, float):
        result['result_number'] = results
    else:
        temp_result = results.split("`")
        result['result_string'] = temp_result[0]
        result['result_number'] = "-"

        for s in temp_result:
            if isinstance(s, float):
                result['result_number'] = s

    return result


def sediment_record(mnemonics, results):
    result = {}
    result['mnemonics'] = mnemonics

    if isinstance(results, float):
        result['result_number'] = results
    else:
        result['result_number'] = "-"
        result['result_string'] = results

    return result


def physical_record(mnemonics, results, ):
    result = {}
    result['mnemonics'] = mnemonics

    if isinstance(results, float):
        result['result_number'] = results
    else:
        result['result_number'] = "-"
        result['result_string'] = results

    return result


def rbc_phase_record(mnemonics, results, ):
    result = {}
    result['mnemonics'] = mnemonics

    if isinstance(results, float):
        result['result_number'] = results
    else:
        result['result_number'] = "-"
        result['result_string'] = results

    return result


def image_record(mnemonics, results):
    result = {}
    result['mnemonics'] = mnemonics

    if isinstance(results, float):
        result['result_number'] = results
    else:
        result['result_number'] = "-"
        result['result_string'] = results

    return result



def create_data(lines: (bytes)) -> list:
    """
    Основная функция (первичной) обработки полученных данных

    :param
        line - список строк данных анализа
    :return:
        results - словарь с содержимым результатов анализа
    """
    try:
        lines = lines.decode()
    except:
        return []
    
    # разделяем строку по &
    RecivedString = lines[:len(lines)-1].split("&")

    # время пробы
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    result_data = {
        "resultDate":date,
        "number": RecivedString[0][3 : len(RecivedString[0])-2],  # берём 1 элемент строки и преобразуем число - это и будет номер пробы
        "results": []
    }


    i = 1
    # разделяем строки на тип анализа, название и результат
    while i < len(RecivedString):
        print(RecivedString[i][2:], RecivedString[i+1][2:], RecivedString[i+2][2:])
        record_type = RecivedString[i][2:]
        # в зависимости от типа обрабатываем результат
        if record_type == "Chemistry":
            result = chemistry_record(RecivedString[i+1][2:], RecivedString[i+2][2:])
        elif record_type == "Sediment":
            result = sediment_record(RecivedString[i+1][2:], RecivedString[i+2][2:])
        elif record_type == "Physical":
            result = physical_record(RecivedString[i+1][2:], RecivedString[i+2][2:])
        elif record_type == "RBC`Phase":
            result = rbc_phase_record(RecivedString[i+1][2:], RecivedString[i+2][2:])
        elif record_type == "Image":
            result = image_record(RecivedString[i+1][2:], RecivedString[i+2][2:])


        result_data['results'].append(result)
        i += 3

    return result_data

    


if __name__ == '__main__':
    pass
