import os
import binascii
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def checksum(dataline) -> bytes:
    """
    Функция подсчета контрольной суммы

    :param
        dataline - строка данных
    :return:
        ascii_sum - контрольная сумма
    """
    # разложение строки на символы (их код-число ASCII)
    new_line = [ord(x) for x in dataline]
    # суммирование значений символов, плюс два конечных символа строки
    new_line_sum = sum(new_line) + 3 + 13  # +ETX = 3, CR = 13
    # получение остатка от деления полученного числа на 256
    new_line_sum_div = new_line_sum % 256
    # получение младшего байта от полученного числа
    new_line_sum_hex_div = new_line_sum_div.to_bytes(1, 'big', signed=False)
    # перевод числа из HEX в Byte
    ascii_sum = binascii.hexlify(new_line_sum_hex_div).upper()
    # print('ascii_sum_div:', ascii_sum_div.upper())
    return ascii_sum


def main_test(data_dict: dict = None, lis_data: dict = None) -> list:
    """
    Основная функция (первичной) обработки полученных данных

    :param
        data_dict - словарь данных от анализатора
        lis_data - словарь данных от ЛИС
    :return:
        message_list - список данных для отправки в анализатор
    """
    # если данные от анализатора не пришли
    if not data_dict:
        data_dict = {}
    order = 1
    message_list = []
    sequence_number = 1

    # Test order data
    specimen_ID = ''
    specimen_ID = data_dict.get('request_info', {}).get('2Q', {}).get('sample_id')

    # b'\x021H|\\^&|||ARCHITECT^9.45^F3452180006^H1P1O1R1C1Q1L1|||||||P|1|20240213164722\r\x032E\r\n'
    # <STX>1H|\^&||||||||||P|1|<CR><ETX>36<CR><LF>
    analyzer_name = data_dict.get('probe_header', {}).get('analyzer_name', '')
    software_version = data_dict.get('probe_header', {}).get('software_version', '')
    analyzer_serial = data_dict.get('probe_header', {}).get('analyzer_serial', '')
    interface_version = data_dict.get('probe_header', {}).get('interface_version', '')
    transmission_date_raw = data_dict.get('probe_header', {}).get('transmission_date_raw', '')
    header_part_1 = rf'"{order}H|\^&|||{analyzer_name}^{software_version}^{analyzer_serial}^{interface_version}|||||||P|1|{transmission_date_raw}"'[
                    1:-1]
    # header_part_1 = '1H|\\^&|||ARCHITECT^9.45^F3452180006^H1P1O1R1C1Q1L1|||||||P|1|20240131155309'
    header_part_2 = checksum(header_part_1)
    header = (header_part_1, header_part_2.decode())
    message_list.append(header)
    order += 1

    # <STX>4Q|1|^129903||^^^ALL||||||||X|<CR><ETX>F3<CR><LF>
    request_part_1 = f'{order}Q|{sequence_number}|^{specimen_ID}||^^^ALL||||||||O'
    request_part_2 = checksum(request_part_1)
    request = (request_part_1, request_part_2.decode())
    if specimen_ID:
        message_list.append(request)
        order += 1

    # <STX>4L|1|||<CR><ETX>B1<CR><LF>
    terminator_part_1 = f'{order}L|1'
    terminator_part_2 = checksum(terminator_part_1)
    terminator = (terminator_part_1, terminator_part_2.decode())
    message_list.append(terminator)
    return message_list


def main(data_dict: dict = None, lis_data: dict = None) -> list:
    """
    Основная функция (первичной) обработки полученных данных

    :param
        data_dict - словарь данных от анализатора
        lis_data - словарь данных от ЛИС
    :return:
        message_list - список данных для отправки в анализатор
    """
    # если данные от анализатора не пришли
    if not data_dict:
        data_dict = {}
    order = 1
    message_list = []

    # Patient data
    sequence_number = 1

    legend = eval(os.getenv('LEGEND'))
    patient_FIO = '^^'
    birth_date = ''
    gender = 'U'
    universal_test_ID = ''
    priority = 'R'
    collection_datetime = None

    if lis_data:
        pacient = lis_data.get('pacient')

        if pacient:
            second_name = pacient.get('d4p1:Surname', '').translate(str.maketrans(legend))
            if isinstance(second_name, dict):
                second_name = ''
            else:
                if len(second_name) > 20:
                    second_name = second_name[:20]
            first_name = pacient.get('d4p1:Name', '').translate(str.maketrans(legend))
            if isinstance(first_name, dict):
                first_name = ''
            else:
                if len(first_name) > 20:
                    first_name = first_name[:20]
            patronymic = pacient.get('d4p1:Patronimic', '').translate(str.maketrans(legend))
            if isinstance(patronymic, dict):
                patronymic = ''
            else:
                if len(patronymic) > 11:
                    patronymic = patronymic[:11]
            patient_FIO = f'{second_name}^{first_name}^{patronymic}'
            gender_id = pacient.get('d4p1:Sex')
            if isinstance(gender_id, dict):
                gender = 'U'
            else:
                try:
                    gender = ['M', 'F', 'U'][int(gender_id) - 1]
                except:
                    gender = 'U'
            birth_date = pacient.get("d4p1:BirthDate")
            if isinstance(birth_date, dict):
                birth_date = ''
            else:
                try:
                    birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
                    birth_date = birth_date.strftime("%Y%m%d")
                except:
                    birth_date = ''
        worklist = lis_data.get('worklist', '')
        if worklist:
            for test_id in worklist:
                if len(universal_test_ID) != 0:
                    universal_test_ID += '\\'
                universal_test_ID += f'^^^{test_id}'
        cito = lis_data.get('cito')
        if cito == 'true':
            priority = 'S'
        collection_datetime = lis_data.get('date', '')
        if collection_datetime:
            collection_datetime = datetime.strptime(collection_datetime, '%Y-%m-%dT%H:%M:%S')
            collection_datetime = collection_datetime.strftime("%Y%m%d%H%M%S")

    practice_PID = ''
    laboratory_PID = ''
    doctor = ''
    clinic_location = ''

    # Test order data
    specimen_ID = data_dict.get('request_info', {}).get('Q', {}).get('sample_id')
    action_code = 'A'
    danger_code = ''
    clinical_information = ''
    specimen_type = ''
    report_types = 'Q'

    # Comment data
    comment_text = ''

    # <STX>1H|\^&||||||||||P|1|<CR><ETX>36<CR><LF>
    header_part_1 = rf'"{order}H|\^&||||||||||P|1|"'[1:-1]
    # header_part_1 = '1H|\\^&|||ARCHITECT^9.45^F3452180006^H1P1O1R1C1Q1L1|||||||P|1|20240131155309'
    header_part_2 = checksum(header_part_1)
    header = (header_part_1, header_part_2.decode())
    message_list.append(header)
    order += 1

    # Send line: ('2P|1||||Testov^Test^Testovich||20040910|M|||||||||||||||||||||||||||', b'2E')
    # <STX>2P|1||||Hrustalev^Mihail^M||19590221|M|||||||||||||||||||||||||||<CR><ETX>BC<CR><LF>
    # <STX>2P|1<CR><ETX>BC<CR><LF>
    if patient_FIO:
        patient_part_1 = (
            f'{order}P|{sequence_number}|{practice_PID}|{laboratory_PID}||{patient_FIO}||{birth_date}|{gender}||'
            f'|||{doctor}||||||||||||{clinic_location}||||||||||')
    else:
        patient_part_1 = (
            f'{order}P|{sequence_number}')
    patient_part_2 = checksum(patient_part_1)
    patient = (patient_part_1, patient_part_2.decode())
    message_list.append(patient)
    order += 1

    # <STX>3O|1|MCC1||^^^16\^^^606|||20010223081223||||A|Hep|lipemic||serum||||||||||Q<CR><ETX>14<CR><LF>
    # <STX>3O|1|1609845074||^^^1023|R||||||A||||||||||||||Q|||||<CR><ETX>14<CR><LF>
    test_order_part_1 = (
        f'{order}O|{sequence_number}|{specimen_ID}||{universal_test_ID}|{priority}||{collection_datetime}||'
        f'||{action_code}|{danger_code}|{clinical_information}||{specimen_type}||||||||||{report_types}|||||')
    test_order_part_2 = checksum(test_order_part_1)
    test_order = (test_order_part_1, test_order_part_2.decode())
    if specimen_ID:
        message_list.append(test_order)
        order += 1

    comment = f'{order}C|{sequence_number}|L|{comment_text}|G'
    if comment_text:
        # comment = comment.encode('utf-8').hex()
        message_list.append(comment)
        order += 1

    # <STX>4Q|1|^129903||^^^ALL||||||||X|<CR><ETX>F3<CR><LF>
    request_part_1 = f'{order}Q|{sequence_number}|^{specimen_ID}||^^^ALL||||||||X|'
    request_part_2 = checksum(request_part_1)
    request = (request_part_1, request_part_2)
    # if specimen_ID:
    #     message_list.append(request)
    #     order += 1

    # <STX>4L|1|||<CR><ETX>B1<CR><LF>
    terminator_part_1 = f'{order}L|1'
    terminator_part_2 = checksum(terminator_part_1)
    terminator = (terminator_part_1, terminator_part_2.decode())
    message_list.append(terminator)
    return message_list


if __name__ == '__main__':
    results = main()
    for result in results:
        print('for result in results', result.encode('utf-8'))
        # print(result)
