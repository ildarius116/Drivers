import logging
import threading

from main.drivers.driver_proxy.models import add_analyze, delete_analyze, get_analyzes, edit_analyze
from main.drivers.driver_proxy.sender_to_driver import send_to_driver
from main.drivers.driver_proxy.drivers.eleven.handler_data import create_data
from main.drivers.driver_proxy.drivers.eleven.handler_soap import create_soap

logger = logging.getLogger(__name__)

# стандартные команды
STX = bytes.fromhex("02")
ETX = bytes.fromhex("03")
LF = bytes.fromhex("0A")
CR = bytes.fromhex("0D")



def transfer_dh100(semaphore: threading, data: bytes, analyzer_name: str, analyzer_number: str, port_parameters: dict):
    """
    Основная функция (первичной) обработки полученных данных
    """
    # если это не стартовое сообщение
    if not STX in data:

        analyze = None
        lines_list = []
        semaphore.acquire()
        # получаем все анализы на анализатор
        all_analyzes = get_analyzes(analyzer_number)
        semaphore.release()

        for analyze in all_analyzes:
            lines_list = analyze.lines_list

            # если в каком-то из анализов нет закрытого символа, то значит для него сейчас происходит обмен данными. 
            if lines_list[-1] != '<ETX>':
                if ETX in data:
                    # добавляем "КОНЕЦ" в список полученных строк
                    lines_list.append('<ETX>')
                    raw_line = analyze.raw_line
                    raw_line += f"{ETX}"
                else:
                    # собираем непреобразованные данные
                    raw_line += data
                    # данные декодируем прежде чем сохранять
                    decoded_data = data.decode()
                    lines_list.append(decoded_data)
                
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


                if STX and ETX in raw_line:
                    # пробуем преобразовать список данных в словарь результатов анализа
                    try:
                        results = create_data(raw_line)
                        logger.info(f"Data getter function eval(result): {results}")
                    except Exception as ex:
                        results = None
                        logger.exception(f"Exception eval(result): \n{ex}")
                        logger.info(f"Data getter function result: {results}")


                    # если преобразование прошло успешно
                    if results:
                            # формирование СОАП отчета о результатах анализа
                            try:
                                results_text = create_soap(data=results, raw_line=raw_line, device_id=analyzer_number)
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
                                logger.info(f"Data : Results not added!")
    # если стартовое сообщение
    elif STX in data:
        # добавляем "СТАРТ" в список полученных строк
        lines_list = ["<STX>", ]

        raw_line = f"{data}"

        logger.info(f"ADD Data into driver's DB: \n"
                    f"Analyzer (name): {analyzer_name}, "
                    f"Analyzer (number): {analyzer_number}, \n"
                    f"Data List: {lines_list}, \n"
                    f"Прямые данные: {raw_line}")
        
        # добавление результатов анализов во временную БД драйвера
        semaphore.acquire()
        add_analyze(analyzer=analyzer_name,
                    device_id=analyzer_number,
                    lines_list=str(lines_list),
                    raw_line=raw_line,
                    )
        semaphore.release()



if __name__ == '__main__':
    pass
