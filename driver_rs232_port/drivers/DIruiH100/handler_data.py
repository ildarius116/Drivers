import re
import logging
from datetime import datetime
import time

# конфигурирование логгера
logger = logging.getLogger(__name__)


def date_record(stroka, date):
    probe = {}
    if len(stroka) == 23:
        # Дата выполнения пробы
        print(stroka[6:23])
        execute_date = time.strptime(stroka[6:22], "%d-%m-%Y %H:%M")
        probe["ProbeDate"] = time.strftime("%Y-%m-%dT%H:%M:%S", execute_date)
    else:
        # Время передачи = текущее время
        transfer_date = date
        probe["ProbeDate"] = transfer_date

    probe["QualityControl"] = "false"
    probe["CITO"] = "false"
    return probe

def serial_number_record(stroka):
    probe = {}
    if len(stroka) > 4:
        probe["SerialNumber"] = stroka[4:]
    else:
        probe["SerialNumber"] = "0"
    return probe

def id_record(stroka):
    probe = {}
    if len(stroka) > 4:
        probe["ProbeNumber"] = stroka[4:]
    else:
        probe["ProbeNumber"] = "0"
    return probe

def result1_record(stroka, date):
    result = {}

    if len(stroka) > 22:
        result["Mnemonics"] = stroka[1:4]
        result["ResultDate"] = date

        if stroka[4:8].strip() != "":
            result["ResultString"] = stroka[4:8]

        # Результаты тестов если число
        if isinstance(stroka[8:16].replace(" ", ""), float):
            result["ResultNumber"] = stroka[8:16]
        else:
            result["ResultNumber"] = "-"
            result["ResultString"] = stroka[4:16]

        # Единицы измерения
        if stroka[16:23] != "    ":
            result["Unit"] = stroka[16:23]

        # Флаг
        if stroka[0:1] == "*":
            result["PatologicFlag"] = "true"
        else:
            result["PatologicFlag"] = "false"

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
    RecivedString = lines.split("\n")

    # время пробы
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    result_data = {
        "resultDate":date,  # берём 1 элемент строки и преобразуем число - это и будет номер пробы
        "results": []
    }


    for s in RecivedString:
        result = None
        if len(s) > 4:
            key = s[1:4]
            if key == "Dat":
                result = date_record(s, date)
            if key == "No.":
                result = serial_number_record(s)
            if key == "ID:":
                result = id_record(s)

            if result:
                result_data.update(result)

            if key in ["UBG", "BIL", "KET", "CRE", "BLD", "PRO", "ALB", "NIT", "LEU", "GLU"]:
                result = result1_record(s, date)
                result_data["results"].append(result)

    return result_data

    

if __name__ == '__main__':
    pass
