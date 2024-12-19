import logging
import threading

from driver_rs232_port.models import add_analyze, delete_analyze, get_analyzes, edit_analyze
from driver_rs232_port.sender_to_driver import send_to_driver
from driver_rs232_port.drivers.i2000sr.handler_data import create_data
from driver_rs232_port.drivers.i2000sr.handler_soap import create_soap
from driver_rs232_port.drivers.i2000sr.handler_worklist import main as worklist_commands_for_driver
from driver_rs232_port.drivers.i2000sr.handler_worklist import main_test as test_worklist_commands_for_driver
from driver_rs232_port.drivers.i2000sr.getter_worklist import get_worklist_from_lis

logger = logging.getLogger(__name__)

# стандартные команды
STX = bytes.fromhex("02")
ETX = bytes.fromhex("03")
EOT = bytes.fromhex("04")
ENQ = bytes.fromhex("05")
ACK = bytes.fromhex("06")
LF = bytes.fromhex("0A")
CR = bytes.fromhex("0D")
NAK = bytes.fromhex("15")
ETB = bytes.fromhex("17")


def main(semaphore: threading, data: bytes, analyzer_name: str, analyzer_number: str, port_parameters: dict):
    """
    Основная функция (первичной) обработки полученных данных
    """
    # если это стартовое сообщение
    if EOT in data:
        logger.info(f"Received EOT in line: {data}")
        analyze = None
        lines_list = []
        semaphore.acquire()
        all_analyzes = get_analyzes(analyzer_number)
        semaphore.release()

        for analyze in all_analyzes:
            lines_list = eval(analyze.lines_list)
            if lines_list[-1] != '<EOT>':
                # добавляем "КОНЕЦ" в список полученных строк
                lines_list.append('<EOT>')
                raw_line = analyze.raw_line
                raw_line += f"{EOT}"

                logger.info(f"Edit Data in driver's DB: \n"
                            f"Analyzer (name): {analyzer_name}, "
                            f"Analyzer (number): {analyzer_number}, \n"
                            f"Data List: {lines_list}, \n"
                            f"Прямые данные: {raw_line}")
                # добавление результатов анализов во временную БД драйвера
                semaphore.acquire()
                edit_analyze(analyze=analyze,
                             lines_list=str(lines_list),
                             raw_line=raw_line,
                             tries=-1,
                             )
                semaphore.release()

        # если список полученных строк более 2, т.е. в нем есть данные проб
        if len(lines_list) > 2:
            # пробуем преобразовать список данных в словарь результатов анализа
            try:
                results = create_data(lines_list)
                logger.info(f"Data getter function eval(result): {results}")
            except Exception as ex:
                results = None
                logger.exception(f"Exception eval(result): \n{ex}")
                logger.info(f"Data getter function result: {results}")

            # если преобразование прошло успешно
            if results:
                for n, result in enumerate(results):
                    if result.get('request_info'):
                        # посылка данных в LIS
                        lis_data = get_worklist_from_lis(data=result, device_id=analyzer_number)
                        logger.info(f"Data from LIS for worklist: {lis_data}")
                        result['lis_data'] = lis_data
                        worklist = worklist_commands_for_driver(result, lis_data)
                        logger.info(f"Worklist data: {worklist}")
                        worklist_test = test_worklist_commands_for_driver(result, lis_data)
                        logger.info(f"Worklist data for analyzer: {worklist_test}")
                        result['worklist'] = worklist
                        result['worklist_test'] = worklist_test

                        for worklist_data in result['worklist']:
                            send_data = b''
                            send_data += STX
                            # строка данных
                            send_data += worklist_data[0].encode()
                            send_data += CR
                            send_data += ETX
                            # контрольная сумма строки данных
                            send_data += worklist_data[1].encode()
                            send_data += CR
                            send_data += LF
                            logger.info(f"Worklist message to Driver: {send_data}")
                            # отправка
                            status = send_to_driver(device_number=analyzer_number,
                                                    device_name=analyzer_name,
                                                    data=send_data,
                                                    port_parameters=port_parameters,
                                                    )
                            if isinstance(status, int) and status == 200:
                                semaphore.acquire()
                                delete_analyze(analyze=analyze)
                                semaphore.release()


                    else:
                        # формирование СОАП отчета о результатах анализа
                        try:
                            results_text = create_soap(data=result, raw_line=raw_line, device_id=analyzer_number)
                        except Exception as ex:
                            results_text = ''
                            logger.exception(f"Exception results_text = eval(set_probes): \n{ex}")
                        # если отчет сформирован
                        if results_text:
                            logger.info(f"Edit Data in driver's DB: \n"
                                        f"Analyzer (name): {analyzer_name}, "
                                        f"Analyzer (number): {analyzer_number}, \n"
                                        f"Probe results: {lines_list}, \n"
                                        f"Прямые данные: {raw_line}")
                            # добавление результатов анализов во временную БД драйвера
                            semaphore.acquire()
                            edit_analyze(analyze=analyze,
                                         probe_results=results_text,
                                         ready_status="True",
                                         tries=-1,
                                         )
                            semaphore.release()

                        # если отчета нет
                        else:
                            logger.info(f"RAW LINE: {raw_line}")
                            logger.info(f"Data №{n}: Results not added!")
            # если было парное сообщение со словом НАЧАЛО, добавляем стартовый символ в список
            if ENQ in data:
                logger.info(f"ADD Data into driver's DB: \n"
                            f"Analyzer (name): {analyzer_name}, "
                            f"Analyzer (number): {analyzer_number}, \n"
                            f"Data List: {['<ENQ>', ]}, \n"
                            f"Прямые данные: {data}")
                # добавление результатов анализов во временную БД драйвера
                semaphore.acquire()
                add_analyze(analyzer=analyzer_name,
                            device_id=analyzer_number,
                            lines_list=str(['<ENQ>', ]),
                            raw_line=f"{data}",
                            )
                semaphore.release()

        # если список полученных строк 2 и менее, при этом, это было парное слово
        elif len(lines_list) <= 2 and ENQ in data:
            # добавляем стартовый символ в список
            logger.info(f"Edit Data in driver's DB: \n"
                        f"Analyzer (name): {analyzer_name}, "
                        f"Analyzer (number): {analyzer_number}, \n"
                        f"Probe results: {lines_list}, \n"
                        f"Data List: , \n"
                        f"Прямые данные: {raw_line}")
            # добавление результатов анализов во временную БД драйвера
            semaphore.acquire()
            edit_analyze(analyze=analyze,
                         lines_list=str(['<ENQ>', ]),
                         raw_line=f"{data}",
                         tries=-1,
                         )
            semaphore.release()

        # в остальных случаях, очищаем список
        else:
            logger.info(f"index else : {data} \nlines_list.clear()")
            logger.info(f"Delete Data in driver's DB: \n")
            # добавление результатов анализов во временную БД драйвера
            if analyze:
                semaphore.acquire()
                delete_analyze(analyze=analyze)
                semaphore.release()

        logger.info(f"Send ACK to Driver")
        send_to_driver(device_number=analyzer_number,
                       device_name=analyzer_name,
                       data=ACK,
                       port_parameters=port_parameters,
                       )
        # если это стартовое сообщение
    elif ENQ in data:
        if ENQ in data and STX in data:
            logger.info(f"Received ENQ and STX: {data}")
        else:
            logger.info(f"Received ENQ: {data}")

        # добавляем "СТАРТ" в список полученных строк
        lines_list = ['<ENQ>', ]
        raw_line = f"{data}"
        # отправка сигнала подтверждения готовности приема
        logger.info(f"Send ACK to Driver")
        send_to_driver(device_number=analyzer_number,
                       device_name=analyzer_name,
                       data=ACK,
                       port_parameters=port_parameters,
                       )
        logger.info(f"ADD Data into driver's DB: \n"
                    f"Analyzer (name): {analyzer_name}, "
                    f"Analyzer (number): {analyzer_number}, \n"
                    f"Data List: {lines_list}, \n"
                    f"Прямые данные: {raw_line}")
        # добавление результатов анализов во временную БД драйвера
        semaphore.acquire()
        add_analyze(analyzer=analyzer_name,
                    device_id=analyzer_number,
                    lines_list=str(['<ENQ>', ]),
                    raw_line=f"{data}",
                    )
        semaphore.release()
        if STX in data:
            stx_handler(semaphore, data, analyzer_number, analyzer_name, port_parameters)

    # если это сообщение с данными
    elif STX in data:
        stx_handler(semaphore, data, analyzer_number, analyzer_name, port_parameters)

    # если это не определенное сообщение
    else:
        logger.info(f"Received raw data: {data}")
        logger.info(f"Send ACK to Driver")
        send_to_driver(device_number=analyzer_number,
                       device_name=analyzer_name,
                       data=ACK,
                       port_parameters=port_parameters,
                       )


def stx_handler(semaphore, data, analyzer_number, analyzer_name, port_parameters):
    logger.info(f"Received STX: {data}")
    lines_list = ['empty']
    semaphore.acquire()
    all_analyzes = get_analyzes(analyzer_number)
    semaphore.release()
    for analyze in all_analyzes:
        lines_list = eval(analyze.lines_list)
        if lines_list[-1] != '<EOT>':
            # добавляем "КОНЕЦ" в список полученных строк
            # добавление полученной строки данных в список данных
            lines_list.append(str(data))
            raw_line = analyze.raw_line
            raw_line += f"{data}"
            logger.info(f"Edit Data in driver's DB: \n"
                        f"Analyzer (name): {analyzer_name}, "
                        f"Analyzer (number): {analyzer_number}, \n"
                        f"Data List: {lines_list}, \n"
                        f"Прямые данные: {raw_line}")
            # добавление результатов анализов во временную БД драйвера
            semaphore.acquire()
            edit_analyze(analyze=analyze,
                         lines_list=str(lines_list),
                         raw_line=raw_line,
                         tries=-1,
                         )
            semaphore.release()

    logger.info(f"lines_list STX: {lines_list}")
    # отправка сигнала подтверждения готовности приема
    logger.info(f"Send ACK to Driver")
    send_to_driver(device_number=analyzer_number,
                   device_name=analyzer_name,
                   data=ACK,
                   port_parameters=port_parameters,
                   )


if __name__ == '__main__':
    pass
