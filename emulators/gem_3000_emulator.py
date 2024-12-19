import serial
import re
import hashlib
import binascii
import threading
import logging
from time import sleep

# from pytz import unicode
STX = bytes.fromhex("02")
ETX = bytes.fromhex("03")
EOT = bytes.fromhex("04")
ENQ = bytes.fromhex("05")
ACK = bytes.fromhex("06")
LF = bytes.fromhex("0A")
CR = bytes.fromhex("0D")
NAK = bytes.fromhex("15")
ETB = bytes.fromhex("17")

ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=5)
ser.isOpen()
logging.basicConfig(level=logging.INFO,
                    # filename='logger.log',
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )

logger = logging.getLogger(__name__)
logger.info(f"Connected to port: {ser.portstr}, "
            f"baudrate: {ser.baudrate}, "
            f"parity: {ser.parity}, "
            f"stopbits: {ser.stopbits}, "
            f"bytesize: {ser.bytesize}, "
            f"timeout: {ser.timeout} "
            )


# ser.write(b'Hello World!\n')
def sender(pause: bool = False):
    start_line = r'\\x02'  # r'<STX>'
    stop_line = r'\\x17'  # r'<ETB>'
    start_sum = r'\\x17'  # r'<ETB>'
    stop_sum = r'\\r\\n'  # r'<CR><LF>'
    finish_line = r'\\x03'  # r'<CR><ETX>'
    finish_sum = r'\\x03'  # r'<ETX>'

    with open('logs/GEM_3000_clear.log', 'r', encoding='utf-8') as file:
        ser.write(ENQ)
        sleep(1)
        for line in file.readlines():
            # line = re.findall(r"\\x02(.*)\\x03", line)
            print('line sender:', line)
            if 'x04' in line:
                print('send <EOT>')
                ser.write(EOT)
                ser.write(CR)
                ser.write(LF)
            else:
                while True:
                    bytesToRead = ser.inWaiting()
                    if bytesToRead:
                        try:
                            line_clear = re.findall(rf"{start_line}(.*){stop_line}", line)[0]
                            check_sum = re.findall(rf"{start_sum}(.*){stop_sum}", line)[0]
                            end_of_transmission = False
                        except IndexError:
                            line_clear = re.findall(rf"{start_line}(.*){finish_line}", line)[0]
                            check_sum = re.findall(rf"{finish_sum}(.*){stop_sum}", line)[0]
                            end_of_transmission = True

                        # print('bytesToRead:', bytesToRead)
                        print('line_clear:', line_clear)
                        # new_line = [x for x in line_clear]
                        # print('new_line:', new_line)
                        new_line = [ord(x) for x in line_clear]
                        # print('new_line:', new_line)
                        new_line_sum = sum(new_line) + 13 + 3
                        # print('new_line_sum:', new_line_sum)
                        new_line_sum_div = new_line_sum % 256
                        # print('new_line_sum_div:', new_line_sum_div)

                        new_line_sum_hex = new_line_sum.to_bytes(4, 'big', signed=False)
                        new_line_sum_hex_div = new_line_sum_div.to_bytes(1, 'big', signed=False)
                        # print('new_line_sum_hex:', new_line_sum_hex)
                        ascii_sum = binascii.hexlify(new_line_sum_hex)
                        # print('ascii_sum:', ascii_sum)
                        ascii_sum_div = binascii.hexlify(new_line_sum_hex_div)
                        # print('ascii_sum_div:', ascii_sum_div)

                        response = ser.readline()
                        # print('response bytesToRead:', response)
                        # print('ACK:', ACK)
                        if ACK in response:
                            # print('Received ACK:', response)
                            # print('line:', line)
                            ser.write(STX)
                            ser.write(line_clear.encode())
                            if end_of_transmission:
                                ser.write(ETX)
                                ser.write(CR)

                            else:
                                ser.write(ETB)
                            ser.write(check_sum.encode())
                            ser.write(CR)
                            ser.write(LF)
                            break


sender()
