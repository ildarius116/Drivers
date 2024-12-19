import os
import binascii
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# стандартные команды
STX = bytes.fromhex("02")
ETX = bytes.fromhex("03")
EOT = bytes.fromhex("04")
ENQ = bytes.fromhex("05")
ACK = bytes.fromhex("06")
LF = bytes.fromhex("0A")
SB = bytes.fromhex("0B")
CR = bytes.fromhex("0D")
NAK = bytes.fromhex("15")
ETB = bytes.fromhex("17")
EB = bytes.fromhex("1C")

VT = bytes.fromhex("0B")
FS = bytes.fromhex("1C")


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


def main(data_dict: dict = None, lis_data: dict = None, message_id: str = None) -> (list, list):
    """
    Основная функция (первичной) обработки полученных данных

    :param
        data_dict - словарь данных от анализатора
        lis_data - словарь данных от ЛИС
    :return:
        message_list - список данных для отправки в анализатор
    """

    data_status = 'OK'
    # если данные от анализатора не пришли
    if not data_dict:
        data_dict = {}
        data_status = 'NF'

    # Patient data
    legend = eval(os.getenv('LEGEND'))
    patient_FIO = '^^'
    birth_date = ''
    gender = 'U'
    universal_test_ID = ''
    priority = 'R'
    collection_datetime = None
    worklist = None

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
                first_name = first_name[0]
                # if len(first_name) > 20:
                #     first_name = first_name[:20]
            patronymic = pacient.get('d4p1:Patronimic', '').translate(str.maketrans(legend))
            if isinstance(patronymic, dict):
                patronymic = ''
            else:
                patronymic = patronymic[0]
                # if len(patronymic) > 11:
                #     patronymic = patronymic[:11]
            patient_FIO = f'{second_name} {first_name}.{patronymic}.'
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
        worklist = lis_data.get('worklist', [])
        # if worklist:
        #     for test_id in worklist:
        #         if len(universal_test_ID) != 0:
        #             universal_test_ID += '\\'
        #         universal_test_ID += f'^^^{test_id}'
        cito = lis_data.get('cito')
        if cito == 'true':
            priority = 'S'
        collection_datetime = lis_data.get('date', '')
        if collection_datetime:
            collection_datetime = datetime.strptime(collection_datetime, '%Y-%m-%dT%H:%M:%S')
            collection_datetime = collection_datetime.strftime("%Y%m%d%H%M%S")

    """ QCK Query Acknowledgment 
    MSH|^~\&|||Mindray||20240415144556||QCK^Q02|53|P|2.3.1||||||ASCII|||<CR> - Message Header
    <CR>
    MSA|AA|53||||0|<CR> - Message Acknowledgment
    <CR>
    ERR|0|<CR> - Error
    <CR>
    QAK|SR|OK|<CR> - Query Acknowledgment
    <CR>
    <FS><CR>
    <CR>
    """
    qck_message_list = [SB.decode()]
    header = rf'"MSH|^~\&|||Mindray||{collection_datetime}||QCK^Q01|{message_id}|P|2.3.1||||||ASCII|||"'[1:-1]
    qck_message_list.append(header)
    qck_message_list.append(CR.decode())
    mack = f"MSA|AA|{message_id}||||0|"
    qck_message_list.append(mack)
    qck_message_list.append(CR.decode())
    err = "ERR|0|"
    qck_message_list.append(err)
    qck_message_list.append(CR.decode())
    qak = f"QAK|SR|{data_status}|"
    qck_message_list.append(qak)
    qck_message_list.append(CR.decode())
    qck_message_list.append(EB.decode())
    qck_message_list.append(CR.decode())

    # Test order data
    specimen_ID = data_dict.get('query_definition', {}).get('sample_bar_code', '')
    patient_ID = data_dict.get('patient_info', {}).get('patient_ID', '')
    time_now = datetime.now().strftime('%Y%m%d%H%M%S')

    """ DSR/ACK: Display response/ Acknowledgment
    MSH|^~\&|||Mindray||20240415144556||DSR^Q03|53|P|2.3.1||||||ASCII|||<CR> - Message Header
    <CR>
    MSA|AA|53||||0|<CR> - Message Acknowledgment
    <CR>
    ERR|0|<CR> - Error
    <CR>
    QAK|SR|OK|<CR> - Query Acknowledgment
    <CR>
    QRD|20240415145212|R|D|32|||RD|539573|OTH|||T|<CR> - Query Definition
    <CR>
    QRF||||||RCT|COR|ALL||<CR> - Query Filter
    <CR>
    DSP|1||p00393029|||<CR> - Display Data
    <CR>
    DSP|2|||||<CR>
    <CR>
    DSP|3||Sabirzyanova`F.`B.|||<CR>
    <CR>
    DSP|4||19610621000000|||<CR>
    <CR>
    DSP|5||F|||<CR>
    <CR>
    DSP|6|||||<CR>
    <CR>
    DSP|7|||||<CR>
    <CR>
    DSP|8|||||<CR>
    <CR>
    DSP|9|||||<CR>
    <CR>
    DSP|10|||||<CR>
    <CR>
    DSP|11|||||<CR>
    <CR>
    DSP|12|||||<CR>
    <CR>
    DSP|13|||||<CR>
    <CR>
    DSP|14|||||<CR>
    <CR>
    DSP|15|||||<CR>
    <CR>
    DSP|16|||||<CR>
    <CR>
    DSP|17|||||<CR>
    <CR>
    DSP|18|||||<CR>
    <CR>
    DSP|19|||||<CR>
    <CR>
    DSP|20|||||<CR>
    <CR>
    DSP|21||539573|||<CR>
    <CR>
    DSP|22|||||<CR>
    <CR>
    DSP|23||20240415141054|||<CR>
    <CR>
    DSP|24||N|||<CR>
    <CR>
    DSP|25|||||<CR>
    <CR>
    DSP|26|||||<CR>
    <CR>
    DSP|27|||||<CR>
    <CR>
    DSP|28|||||<CR>
    <CR>
    DSP|29||11^^^|||<CR>
    <CR>
    DSP|30||10^^^|||<CR>
    <CR>
    DSC||<CR> - Continuation Pointer
    <CR>
    <FS><CR>
    <CR>
    """
    dsr_message_list = [SB.decode()]
    header = rf'"MSH|^~\&|||Mindray||{collection_datetime}||DSR^Q03|{message_id}|P|2.3.1||||||ASCII|||"'[1:-1]
    dsr_message_list.append(header)
    dsr_message_list.append(CR.decode())
    mack = f"MSA|AA|{message_id}||||0|"
    dsr_message_list.append(mack)
    dsr_message_list.append(CR.decode())
    err = "ERR|0|"
    dsr_message_list.append(err)
    dsr_message_list.append(CR.decode())
    qak = f"QAK|SR|{data_status}|"
    dsr_message_list.append(qak)
    dsr_message_list.append(CR.decode())
    qrd = f"QRD|{collection_datetime}|{priority}|D|{message_id}|||RD|{specimen_ID}|OTH|||T|"
    dsr_message_list.append(qrd)
    dsr_message_list.append(CR.decode())
    qrf = "QRF||||||RCT|COR|ALL||"
    dsr_message_list.append(qrf)
    dsr_message_list.append(CR.decode())
    dsp = f"DSP|1||{patient_ID}|||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|2|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = f"DSP|3||{patient_FIO}|||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = f"DSP|4||{birth_date}|||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = f"DSP|5||{gender}|||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|6|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|7|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|8|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|9|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|10|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|11|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|12|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|13|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|14|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|15|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|16|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|17|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|18|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|19|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|20|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = f"DSP|21||{specimen_ID}|||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|22|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = f"DSP|23||{time_now}|||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|24||N|||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|25|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|26|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|27|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp = "DSP|28|||||"
    dsr_message_list.append(dsp)
    dsr_message_list.append(CR.decode())
    dsp_num = 29
    if worklist:
        for n, test_id in enumerate(worklist):
            dsp_num += n
            dsp = f"DSP|{dsp_num}||{test_id}^^^|||"
            dsr_message_list.append(dsp)
            dsr_message_list.append(CR.decode())
    dsc = "DSC||"
    dsr_message_list.append(dsc)
    dsr_message_list.append(CR.decode())
    dsr_message_list.append(EB.decode())
    dsr_message_list.append(CR.decode())

    return qck_message_list, dsr_message_list


if __name__ == '__main__':
    results = main()
    for result in results:
        print('for result in results', result.encode('utf-8'))
        # print(result)
