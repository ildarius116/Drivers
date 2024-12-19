import logging
import datetime
import threading

from driver_rs232_port.models import Analyzes, add_analyze, edit_analyze
from driver_rs232_port.sender_to_driver import send_to_driver
from driver_rs232_port.drivers.bc_30s.handler_data import create_data
from driver_rs232_port.drivers.bc_30s.handler_soap import create_soap

logger = logging.getLogger(__name__)

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


def ack_command(message_id: str = '') -> str:
    """
    Пример:
    MSH|^~\&|Mindray||||20240415145212||ACK^Q03|52|P|2.3.1||||||ASCII|||<CR>
    MSA|AA|52|Message`accepted|||0|<CR>
    ERR|0|<CR>
    <FS><CR>
    """
    ack_list = [SB.decode()]
    time_now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    msh = f"MSH|^~\&|Mindray||||{time_now}||ACK^Q03|{message_id}|P|2.3.1||||||ASCII|||"
    ack_list.append(msh)
    ack_list.append(CR.decode())
    msa = f"MSA|AA|{message_id}|Message`accepted|||0|"
    ack_list.append(msa)
    ack_list.append(CR.decode())
    # err = f"ERR|0|"
    # ack_list.append(err)
    # ack_list.append(CR.decode())
    ack_list.append(EB.decode())
    ack_list.append(CR.decode())
    ack_str = ''.join(ack_list)
    return ack_str


def main(semaphore: threading, data: bytes, analyzer_name: str, analyzer_number: str, port_parameters: dict):
    """
    Основная функция (первичной) обработки полученных данных
    """
    # TODO
    #  возможно, не нужно
    # проверяем, если это просто одиночное стартовое слово
    if data == SB:
        logger.info(f"main data SB: {data}")
        print(f"Send ACK to Driver")
        logger.info(f"Send ACK to Driver")
        send_to_driver(device_number=analyzer_number,
                       device_name=analyzer_name,
                       data=ACK,
                       port_parameters=port_parameters,
                       )
    # проверяем, если это пустое сообщение
    elif data == b"":
        pass
    # в остальных случаях
    else:
        logger.info(f"main data: {data}")
        # создаем рабочую строку прямых данных
        str_data = str(data)
        str_data = str_data.replace("b", '')
        str_data = str_data.replace("'", '')

        buffer = None
        semaphore.acquire()
        # смотрим, есть ли уже в буфере строка прямых данных
        buffers = Analyzes.get_all_buffers()
        if buffers:
            for buffer in buffers:
                # если есть, то добавляем текущую строку к уже имеющейся в (полученной из) БД
                str_data = buffer.raw_line + str_data
                # добавляем полученную строку в БД
                logger.info(f"Edit Data in BUFFER: \n"
                            f"Analyzer (name): {analyzer_name}, "
                            f"Analyzer (number): {analyzer_number}, \n"
                            f"Прямые данные: {str_data}")
                edit_analyze(analyze=buffer,
                             raw_line=str_data,
                             tries=-1,
                             )
        # если строки данных в буфере нет
        else:
            # добавление рабочей строки в буфер БД драйвера
            logger.info(f"ADD Data into BUFFER: \n"
                        f"Analyzer (name): {analyzer_name}, "
                        f"Analyzer (number): {analyzer_number}, \n"
                        f"Прямые данные: {str_data}")
            buffer = add_analyze(analyzer=analyzer_name,
                                 device_id=analyzer_number,
                                 raw_line=str_data,
                                 buffer=True,
                                 )
        semaphore.release()

        # ищем индексы местоположение начального и конечного слов строки сообщения
        find_enq = str_data.find("MSH")
        find_eot = str_data.find(r'\x1c\r')
        # если индексы найдены и они в правильном порядке
        if find_enq >= 0 and find_eot > 0 and (find_enq < find_eot):
            # обрезаем из рабочей строки необходимую часть (цельное сообщение)
            raw_data = str_data[:find_eot + 6]
            raw_data = raw_data[find_enq:]
            # удаляем из рабочей строки полученное сообщение
            str_data = str_data[find_eot + 6:]
            # создаем список строк для обработки данных
            lines_list = ['<ENQ>']
            lines_list.extend(raw_data.split(r'\r'))
            lines_list.append('<EOT>')
            # получаем номер сообщения анализатора
            message_id = raw_data.split('|')[9]
            # получаем номер сообщения анализатора
            message_type = raw_data.split('|')[8]
            # создаем новую запись в БД
            logger.info(f"ADD Data into driver's DB: \n"
                        f"Analyzer (name): {analyzer_name}, "
                        f"Analyzer (number): {analyzer_number},\n"
                        f"Номер сообщения: {message_id},\n"
                        f"Data List: {lines_list},\n"
                        f"Прямые данные: {raw_data}")
            semaphore.acquire()
            current_analyze = add_analyze(analyzer=analyzer_name,
                                          device_id=analyzer_number,
                                          lines_list=str(lines_list),
                                          raw_line=raw_data,
                                          message_id=message_id,
                                          )
            semaphore.release()

            if buffer:
                # редактируем буферную запись обновленной рабочей строкой
                logger.info(f"Edit Data in BUFFER: \n"
                            f"Analyzer (name): {analyzer_name}, "
                            f"Analyzer (number): {analyzer_number}, \n"
                            f"Прямые данные: {str_data}")
                semaphore.acquire()
                edit_analyze(analyze=buffer,
                             raw_line=str_data,
                             tries=-1,
                             )
                semaphore.release()

            # пробуем преобразовать список данных в словарь результатов анализа
            try:
                results = create_data(lines_list)
                logger.info(f"Create_data function result: {results}")
            except Exception as ex:
                results = None
                logger.exception(f"Exception Create_data: \n{ex}")
                logger.info(f"Create_data function result: {results}")

            # если преобразование прошло успешно
            if results:
                for n, result in enumerate(results):
                    # формирование СОАП отчета о результатах анализа
                    try:
                        results_text = create_soap(data=result, raw_line=raw_data, device_id=analyzer_number)
                    except Exception as ex:
                        results_text = ''
                        logger.exception(f"Exception results_text = eval(set_probes): \n{ex}")
                    # если отчет сформирован
                    if results_text:
                        logger.info(f"Edit Data in driver's DB: \n"
                                    f"Analyzer (name): {analyzer_name}, "
                                    f"Analyzer (number): {analyzer_number}, \n"
                                    f"Probe results: {lines_list}, \n"
                                    f"Прямые данные: {raw_data}")
                        # добавление результатов анализов во временную БД драйвера
                        semaphore.acquire()
                        edit_analyze(analyze=current_analyze,
                                     probe_results=results_text,
                                     ready_status="True",
                                     tries=-1,
                                     )
                        semaphore.release()

                    # если отчета нет
                    else:
                        logger.info(f"RAW LINE: {raw_data}")
                        logger.info(f"Data №{n}: Results not added!")

            # отправка подтверждения приема сообщения
            logger.info(f"Send ACK to Driver")
            send_to_driver(device_number=analyzer_number,
                           device_name=analyzer_name,
                           data=ack_command(message_id).encode(),
                           port_parameters=port_parameters,
                           )


if __name__ == '__main__':
    pass
