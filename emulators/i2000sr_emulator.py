import re
import serial
import binascii
import logging

from time import sleep

STX = bytes.fromhex("02")
ETX = bytes.fromhex("03")
EOT = bytes.fromhex("04")
ENQ = bytes.fromhex("05")
ACK = bytes.fromhex("06")
LF = bytes.fromhex("0A")
CR = bytes.fromhex("0D")
NAK = bytes.fromhex("15")
ETB = bytes.fromhex("17")

# ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, bytesize=serial.EIGHTBITS,
#                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=5)
ser = serial.Serial(port='COM6', baudrate=9600, bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=5)
ser.isOpen()
logger = logging.getLogger(__name__)
# конфигурирование логгера
logging.basicConfig(level=logging.INFO,
                    # filename='emulator_logger.log',
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )
logger.info(f"Connected to port: {ser.portstr}, "
            f"baudrate: {ser.baudrate}, "
            f"parity: {ser.parity}, "
            f"stopbits: {ser.stopbits}, "
            f"bytesize: {ser.bytesize}, "
            f"timeout: {ser.timeout} "
            )


def sender_worklist():
    start_line = r'<STX>'
    stop_line = r'<CR><ETX>'
    start_sum = r'<ETX>'
    stop_sum = r'<CR><LF>'

    with open('logs/em_log_architect_i2000SR_02.log', 'r', encoding='windows-1251') as file:
        for line in file.readlines():
            print('line sender:', line)
            if '<ENQ>' in line:
                print('send <ENQ>')
                ser.write(ENQ)
                ser.write(CR)
                ser.write(LF)
            elif '<EOT>' in line:
                print('send <EOT>')
                ser.write(EOT)
                ser.write(CR)
                ser.write(LF)
            else:
                while True:
                    bytesToRead = ser.inWaiting()
                    line_clear = re.findall(rf"{start_line}(.*){stop_line}", line)
                    line_clear = line_clear[0]
                    line_clear = line_clear.replace('`', ' ')
                    check_sum = re.findall(rf"{start_sum}(.*){stop_sum}", line)[0]

                    if bytesToRead:
                        new_line = [ord(x) for x in line_clear]
                        # print('new_line:', new_line)
                        new_line_sum = sum(new_line) + 3 + 13  # +ETX = 3, CR = 13
                        # print('new_line_sum:', new_line_sum)
                        new_line_sum_div = new_line_sum % 256
                        # print('new_line_sum_div:', new_line_sum_div)
                        new_line_sum_hex = new_line_sum.to_bytes(4, 'big', signed=False)
                        new_line_sum_hex_div = new_line_sum_div.to_bytes(1, 'big', signed=False)
                        # print('new_line_sum_hex:', new_line_sum_hex)
                        # print('new_line_sum_hex_div:', new_line_sum_hex_div)
                        ascii_sum = binascii.hexlify(new_line_sum_hex)
                        # print('ascii_sum:', ascii_sum)
                        ascii_sum_div = binascii.hexlify(new_line_sum_hex_div)
                        # print('ascii_sum_div:', ascii_sum_div)

                        response = ser.readline()
                        if ACK in response:
                            ser.write(STX)
                            ser.write(line_clear.encode())
                            ser.write(CR)
                            ser.write(ETX)
                            ser.write(check_sum.encode())
                            ser.write(CR)
                            ser.write(LF)
                            break


def sender_results():
    start_line = r'<STX>'
    stop_line = r'<CR><ETX>'
    start_sum = r'<ETX>'
    stop_sum = r'<CR><LF>'
    with open('logs/em_log_architect_i2000SR_03.log', 'r', encoding='windows-1251') as file:
        for line in file.readlines():
            print('line sender:', line)
            if '<ENQ>' in line:
                print('send <ENQ>')
                ser.write(ENQ)
                ser.write(CR)
                ser.write(LF)
            elif '<EOT>' in line:
                print('send <EOT>')
                ser.write(EOT)
                ser.write(CR)
                ser.write(LF)
            else:
                while True:
                    bytesToRead = ser.inWaiting()
                    line_clear = re.findall(rf"{start_line}(.*){stop_line}", line)
                    line_clear = line_clear[0]
                    line_clear = line_clear.replace('`', ' ')
                    check_sum = re.findall(rf"{start_sum}(.*){stop_sum}", line)[0]

                    if bytesToRead:
                        print('line_clear:', line_clear)
                        new_line = [ord(x) for x in line_clear]
                        new_line_sum = sum(new_line) + 3 + 13  # +ETX = 3, CR = 13
                        new_line_sum_div = new_line_sum % 256
                        new_line_sum_hex_div = new_line_sum_div.to_bytes(1, 'big', signed=False)
                        ascii_sum_div = binascii.hexlify(new_line_sum_hex_div)
                        print('ascii_sum_div:', ascii_sum_div)

                        response = ser.readline()
                        if ACK in response:
                            ser.write(STX)
                            ser.write(line_clear.encode())
                            ser.write(CR)
                            ser.write(ETX)
                            ser.write(check_sum.encode())
                            ser.write(CR)
                            ser.write(LF)
                            break


def receiver_simple():
    # i = 1
    while True:
        bytesToRead = ser.inWaiting()
        # print('bytesToRead:', bytesToRead)
        if bytesToRead:
            # print('bytesToRead:', bytesToRead)
            response = ser.readline()
            print('response:', response)
            print('response.hex:', response.hex())
            # print('response.hex:', response)
            # print('response.decode: ', response.decode())
            line_clear = re.sub(r"[\\]{2,}", r'\\', str(response))
            print('line_clear:', line_clear)
            # if i == 3:
            #     print('i = 4')
            #     sender()
            print('\nACK: ', ACK)
            ser.write(ACK)
            ser.write(CR)
            ser.write(LF)
            # i += 1


def receiver_worklist():
    i = 1
    raw_lines_list = []
    lines_list = []
    while True:
        bytesToRead = ser.inWaiting()
        # print('bytesToRead:', bytesToRead)
        if bytesToRead:
            # print('bytesToRead:', bytesToRead)
            line = ser.readline()
            # print(f"Received bytesToRead: {line} - {type(line)}")
            # print(f"ENQ: {ENQ} - {type(ENQ)}")
            # logger.info(f"Received bytesToRead: {line} - {type(line)}")
            # logger.info(f"ENQ: {ENQ} - {type(ENQ)}")

            if ENQ in line:
                lines_list.clear()
                lines_list = ['<ENQ>', ]
                logger.info(f"Received ENQ: {line}")
                print(f"Received ENQ: {line}")
                # отправка сигнала подтверждения готовности приема
                logger.info(f"Send ACK")
                ser.write(ACK)
                ser.write(CR)
                ser.write(LF)
            elif EOT in line:
                lines_list.append('<EOT>')
                logger.info(f"Received EOT: {line}")
                print(f"Received EOT: {line}")

                # отправка сигнала подтверждения готовности приема
                logger.info(f"Send ACK")
                ser.write(ACK)
                ser.write(CR)
                ser.write(LF)
                # вызов функции обработки полученных данных
                worklist_dict = worklist_handler(lines_list)
                logger.info(f"RESULT: {worklist_dict}")
                print(f"RESULT: {worklist_dict}")
                # if worklist_dict.get('worklist'):
                #     # worklist = worklist_dict.get('worklist')
                #     # sender(worklist)
                sender_results()
                return

            elif STX in line:
                logger.info(f"Received STX: {line}")
                logger.info(f"Received line.decode(): {line}")
                print(f"Received STX: {line}")
                line = re.sub(r"[\\]{2,}", r'\\', str(line))
                print(f"Clear line: {line}")
                # добавление полученной строки данных в список данных
                lines_list.append(line)
                # lines_list.append(line.decode())
                # отправка сигнала подтверждения готовности приема
                logger.info(f"Send ACK")
                ser.write(ACK)
                ser.write(CR)
                ser.write(LF)
            else:
                logger.info(f"Received raw data: {line}")
                print(f"Received raw data: {line}")

                logger.info(f"Send ACK")
                ser.write(ACK)
                ser.write(CR)
                ser.write(LF)


def worklist_handler(lines):
    """
    Основная функция (первичной) обработки полученных данных
    """
    # print(data)
    results = {}
    # print('lines_main:', lines)
    for line in lines:
        # print('\nline:', line.replace('\n', ''))
        # print('line_main:', line)
        # сообщение о начале передачи сообщений
        if '<ENQ>' in line:
            print('Start transmitting')
            # шаблон для результатов анализа
            results = {
                "worklist": []
            }
        # сообщение о завершении передачи сообщений
        elif '<EOT>' in line:
            print('Stop transmitting')
            return results
        # все прочие сообщения
        else:
            pattern = r"\\x02(.*)\\r\\x03"
            data = re.findall(pattern, line)[0]
            # превращение её в список
            data = re.split(r'[|]', data)
            if 'O' in data[0]:
                worklist_line = data[4]
                worklist_line = worklist_line.replace('^', '')
                worklist = worklist_line.split('\\')
                # # запись временных данных в общий шаблон результатов анализа
                results['worklist'] = worklist
            # print('results:', results)
    return results


print('sender_worklist ... ')
sender_worklist()
sleep(1)
print('receiver_worklist ... ')
receiver_worklist()
sleep(1)
# print('sender_results ... ')
# sender_results()
# sleep(1)
# print('receiver ... ')
# receiver()


# ser.write(ACK)
# print('\nACK_ACK_ACK_ACK_ACK: ', ACK)
# ser.write(CR)
# ser.write(LF)
# sleep(1)
# print('receiver ... ')
# receiver()
